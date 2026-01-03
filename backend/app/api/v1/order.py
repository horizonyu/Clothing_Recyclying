"""
订单API - 核心业务逻辑
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import json
import base64
import hmac
import hashlib
import uuid

from app.db.database import get_db
from app.config import settings
from app.models.user import User
from app.models.device import Device
from app.models.order import DeliveryOrder
from app.models.wallet import WalletRecord
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.order import (
    ScanQrcodeRequest,
    ScanQrcodeResponse,
    ClaimOrderResponse,
    OrderListItem,
    OrderDetailResponse,
    OrderStatsResponse
)
from app.api.deps import get_current_user

router = APIRouter()


def generate_order_id() -> str:
    """生成订单ID"""
    return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


def generate_record_id() -> str:
    """生成记录ID"""
    return f"REC{uuid.uuid4().hex[:12].upper()}"


def verify_signature(data: dict, signature: str, device_secret: str) -> bool:
    """验证二维码签名"""
    # 拼接待签名字符串
    sign_str = f"{data['v']}.{data['d']}.{data['vid']}.{data['w']}.{data['p']}.{data['a']}.{data['t']}.{data['e']}"
    # 计算HMAC-SHA256
    expected_sig = hmac.new(
        device_secret.encode(),
        sign_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature)


@router.post("/scan", response_model=ResponseModel)
async def scan_qrcode(
    request: ScanQrcodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    扫码解析投递凭证
    
    二维码内容格式(Base64编码的JSON):
    {
        "v": 1,              // 版本号
        "d": "DEV001",       // 设备ID
        "vid": "V20260102DEV001001",  // 凭证ID
        "w": 3500,           // 重量(克)
        "p": 30,             // 单价(分/kg)
        "a": 105,            // 金额(分)
        "t": 1704182396,     // 生成时间戳
        "e": 1704182996,     // 过期时间戳
        "s": "签名"          // HMAC-SHA256签名
    }
    """
    try:
        # 解析Base64编码的二维码数据
        qr_json = base64.b64decode(request.qrcode_data).decode('utf-8')
        qr_data = json.loads(qr_json)
    except Exception:
        raise HTTPException(status_code=400, detail={"code": 10006, "message": "二维码数据格式错误"})
    
    # 检查必要字段
    required_fields = ['v', 'd', 'vid', 'w', 'p', 'a', 't', 'e', 's']
    if not all(field in qr_data for field in required_fields):
        raise HTTPException(status_code=400, detail={"code": 10006, "message": "二维码数据不完整"})
    
    device_id = qr_data['d']
    voucher_id = qr_data['vid']
    signature = qr_data['s']
    
    # 检查是否过期
    if datetime.now().timestamp() > qr_data['e']:
        raise HTTPException(status_code=400, detail={"code": 10004, "message": "二维码已过期"})
    
    # 查询设备
    result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=400, detail={"code": 10002, "message": "设备不存在"})
    
    # 验证签名
    if not verify_signature(qr_data, signature, device.device_secret):
        raise HTTPException(status_code=400, detail={"code": 10007, "message": "签名验证失败"})
    
    # 查询订单是否已存在
    result = await db.execute(
        select(DeliveryOrder).where(DeliveryOrder.voucher_id == voucher_id)
    )
    order = result.scalar_one_or_none()
    
    if order:
        # 订单已存在，检查状态
        if order.status == 1:
            raise HTTPException(status_code=400, detail={"code": 10003, "message": "该订单已被领取"})
        elif order.status == 2:
            raise HTTPException(status_code=400, detail={"code": 10004, "message": "二维码已过期"})
    else:
        # 创建新订单
        weight = qr_data['w'] / 1000  # 克转公斤
        unit_price = qr_data['p'] / 100  # 分转元
        amount = qr_data['a'] / 100  # 分转元
        carbon_reduction = weight * settings.CARBON_COEFFICIENT
        points = int(carbon_reduction * settings.POINTS_COEFFICIENT)
        
        order = DeliveryOrder(
            order_id=generate_order_id(),
            voucher_id=voucher_id,
            device_id=device_id,
            device_name=device.name,
            device_address=device.address,
            weight=weight,
            unit_price=unit_price,
            amount=amount,
            carbon_reduction=carbon_reduction,
            points_earned=points,
            signature=signature,
            status=0,
            qrcode_time=datetime.fromtimestamp(qr_data['t']),
            qrcode_expire_time=datetime.fromtimestamp(qr_data['e'])
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
    
    # 记录扫码时间
    order.scan_time = datetime.now()
    await db.commit()
    
    return ResponseModel(data=ScanQrcodeResponse(
        order_id=order.order_id,
        voucher_id=order.voucher_id,
        device_id=order.device_id,
        device_name=order.device_name or "",
        weight=order.weight,
        unit_price=order.unit_price,
        amount=order.amount,
        carbon_reduction=order.carbon_reduction,
        points=order.points_earned,
        status=order.status,
        qrcode_time=order.qrcode_time,
        expire_time=order.qrcode_expire_time
    ))


@router.post("/{order_id}/claim", response_model=ResponseModel)
async def claim_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """领取订单金额"""
    # 查询订单
    result = await db.execute(
        select(DeliveryOrder).where(DeliveryOrder.order_id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order.status == 1:
        raise HTTPException(status_code=400, detail={"code": 10003, "message": "订单已被领取"})
    
    if order.status == 2:
        raise HTTPException(status_code=400, detail={"code": 10004, "message": "订单已过期"})
    
    # 检查是否过期
    if order.qrcode_expire_time and datetime.now() > order.qrcode_expire_time:
        order.status = 2
        await db.commit()
        raise HTTPException(status_code=400, detail={"code": 10004, "message": "订单已过期"})
    
    # 更新订单状态
    order.user_id = current_user.user_id
    order.status = 1
    order.claim_time = datetime.now()
    
    # 更新用户余额
    balance_before = current_user.balance
    current_user.balance += order.amount
    current_user.points += order.points_earned
    current_user.total_weight += order.weight
    current_user.total_carbon += order.carbon_reduction
    current_user.total_count += 1
    
    # 创建钱包记录
    wallet_record = WalletRecord(
        record_id=generate_record_id(),
        user_id=current_user.user_id,
        type="income",
        amount=order.amount,
        balance_before=balance_before,
        balance_after=current_user.balance,
        order_id=order.order_id,
        remark=f"回收收入-{order.device_name}"
    )
    db.add(wallet_record)
    
    await db.commit()
    
    return ResponseModel(data=ClaimOrderResponse(
        order_id=order.order_id,
        amount=order.amount,
        weight=order.weight,
        carbon_reduction=order.carbon_reduction,
        points_earned=order.points_earned,
        wallet_balance=current_user.balance
    ))


@router.get("/list", response_model=ResponseModel)
async def get_order_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单列表"""
    query = select(DeliveryOrder).where(
        DeliveryOrder.user_id == current_user.user_id
    )
    
    if status is not None:
        query = query.where(DeliveryOrder.status == status)
    
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # 分页查询
    query = query.order_by(DeliveryOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    items = [
        OrderListItem(
            order_id=o.order_id,
            device_name=o.device_name or "",
            weight=o.weight,
            amount=o.amount,
            carbon_reduction=o.carbon_reduction,
            status=o.status,
            created_at=o.created_at
        )
        for o in orders
    ]
    
    return ResponseModel(data=PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.get("/stats", response_model=ResponseModel)
async def get_order_stats(
    current_user: User = Depends(get_current_user)
):
    """获取订单统计"""
    return ResponseModel(data=OrderStatsResponse(
        total_count=current_user.total_count,
        total_weight=current_user.total_weight,
        total_amount=current_user.balance + (current_user.frozen_balance or 0),
        total_carbon=current_user.total_carbon
    ))


@router.get("/{order_id}/detail", response_model=ResponseModel)
async def get_order_detail(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单详情"""
    result = await db.execute(
        select(DeliveryOrder).where(
            DeliveryOrder.order_id == order_id,
            DeliveryOrder.user_id == current_user.user_id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    return ResponseModel(data=OrderDetailResponse(
        order_id=order.order_id,
        voucher_id=order.voucher_id,
        device_id=order.device_id,
        device_name=order.device_name or "",
        device_address=order.device_address,
        weight=order.weight,
        unit_price=order.unit_price,
        amount=order.amount,
        carbon_reduction=order.carbon_reduction,
        points_earned=order.points_earned,
        status=order.status,
        created_at=order.created_at,
        claim_time=order.claim_time
    ))

