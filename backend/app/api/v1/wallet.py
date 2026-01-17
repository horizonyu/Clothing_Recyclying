"""
钱包API
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.db.database import get_db
from app.models.user import User
from app.models.wallet import WalletRecord
from app.models.withdraw import WithdrawRecord, WithdrawStatus
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.user import (
    WalletBalanceResponse,
    WalletRecordItem,
    WithdrawRequest
)
from app.api.deps import get_current_user
from app.services.wechat_pay import wechat_pay_service

router = APIRouter()


@router.get("/balance", response_model=ResponseModel)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user)
):
    """获取钱包余额"""
    available = current_user.balance - (current_user.frozen_balance or 0)
    
    return ResponseModel(data=WalletBalanceResponse(
        balance=current_user.balance,
        frozen_balance=current_user.frozen_balance or 0,
        available_balance=max(0, available),
        points=current_user.points
    ))


@router.get("/records", response_model=ResponseModel)
async def get_wallet_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取交易记录"""
    query = select(WalletRecord).where(
        WalletRecord.user_id == current_user.user_id
    )
    
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # 分页查询
    query = query.order_by(WalletRecord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    records = result.scalars().all()
    
    items = [
        WalletRecordItem(
            id=r.record_id,
            type=r.type,
            amount=r.amount,
            created_at=r.created_at,
            remark=r.remark
        )
        for r in records
    ]
    
    return ResponseModel(data=PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.post("/withdraw", response_model=ResponseModel)
async def withdraw(
    request: WithdrawRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """申请提现到微信零钱"""
    # 检查金额
    if request.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail={"code": 20003, "message": "提现金额必须大于0"}
        )
    
    if request.amount < 1:
        raise HTTPException(
            status_code=400,
            detail={"code": 20002, "message": "最低提现金额为1元"}
        )
    
    # 检查可用余额
    available = current_user.balance - (current_user.frozen_balance or 0)
    if request.amount > available:
        raise HTTPException(
            status_code=400,
            detail={"code": 20001, "message": "余额不足"}
        )
    
    # 只支持微信提现
    if request.channel != "wechat":
        raise HTTPException(
            status_code=400,
            detail={"code": 20004, "message": "目前仅支持提现到微信零钱"}
        )
    
    # 检查微信支付服务是否可用
    if not wechat_pay_service.is_available():
        raise HTTPException(
            status_code=500,
            detail={"code": 20005, "message": "提现服务暂时不可用，请稍后重试"}
        )
    
    # 检查用户是否已绑定微信OpenID
    if not current_user.openid:
        raise HTTPException(
            status_code=400,
            detail={"code": 20006, "message": "未绑定微信账号，无法提现"}
        )
    
    # 生成提现单号
    withdraw_id = f"WD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    
    try:
        # 1. 创建提现记录
        withdraw_record = WithdrawRecord(
            withdraw_id=withdraw_id,
            user_id=current_user.user_id,
            amount=request.amount,
            channel=request.channel,
            status=WithdrawStatus.PENDING.value,
            wechat_openid=current_user.openid
        )
        db.add(withdraw_record)
        await db.flush()  # 获取ID
        
        # 2. 冻结金额
        balance_before = current_user.balance
        current_user.frozen_balance = (current_user.frozen_balance or 0) + request.amount
        balance_after = current_user.balance
        
        # 3. 创建钱包冻结记录
        freeze_record_id = f"FR{uuid.uuid4().hex[:28].upper()}"
        wallet_record = WalletRecord(
            record_id=freeze_record_id,
            user_id=current_user.user_id,
            type="freeze",  # 冻结类型
            amount=-request.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            remark=f"提现冻结-{withdraw_id}"
        )
        db.add(wallet_record)
        
        await db.commit()
        
        # 4. 调用微信转账接口
        try:
            transfer_result = await wechat_pay_service.transfer_to_balance(
                openid=current_user.openid,
                amount=request.amount,
                description="旧衣回收收益提现",
                withdraw_id=withdraw_id
            )
            
            # 5. 更新提现记录状态（转账成功）
            withdraw_record.status = WithdrawStatus.SUCCESS.value
            withdraw_record.wechat_batch_id = transfer_result.get("batch_id")
            withdraw_record.completed_at = datetime.now()
            
            # 6. 扣除余额（转账成功，实际扣除）
            balance_before = current_user.balance
            current_user.balance = balance_before - request.amount
            current_user.frozen_balance = (current_user.frozen_balance or 0) - request.amount
            balance_after = current_user.balance
            
            # 7. 创建钱包支出记录
            withdraw_record_id = f"WD{uuid.uuid4().hex[:28].upper()}"
            wallet_withdraw = WalletRecord(
                record_id=withdraw_record_id,
                user_id=current_user.user_id,
                type="withdraw",
                amount=-request.amount,
                balance_before=balance_before,
                balance_after=balance_after,
                remark=f"提现-{withdraw_id}"
            )
            db.add(wallet_withdraw)
            
            await db.commit()
            
            logger.info(f"提现成功: withdraw_id={withdraw_id}, amount={request.amount}, user={current_user.user_id}")
            
            return ResponseModel(
                message="提现申请已提交，资金将即时到账",
                data={
                    "withdraw_id": withdraw_id,
                    "amount": request.amount,
                    "channel": request.channel,
                    "status": "processing",
                    "batch_id": transfer_result.get("batch_id")
                }
            )
            
        except Exception as e:
            # 转账失败，回滚冻结金额
            logger.error(f"微信转账失败: {e}")
            
            # 回滚冻结
            current_user.frozen_balance = (current_user.frozen_balance or 0) - request.amount
            
            # 更新提现记录
            withdraw_record.status = WithdrawStatus.FAILED.value
            withdraw_record.error_message = str(e)
            
            # 删除冻结记录
            await db.delete(wallet_record)
            
            await db.commit()
            
            raise HTTPException(
                status_code=500,
                detail={"code": 20007, "message": f"提现失败: {str(e)}"}
            )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"提现处理异常: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": 20008, "message": "提现处理失败，请稍后重试"}
        )

