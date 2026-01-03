"""
钱包API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.models.user import User
from app.models.wallet import WalletRecord
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.user import (
    WalletBalanceResponse,
    WalletRecordItem,
    WithdrawRequest
)
from app.api.deps import get_current_user

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
    """申请提现"""
    # 检查金额
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="提现金额必须大于0")
    
    if request.amount < 1:
        raise HTTPException(
            status_code=400, 
            detail={"code": 20002, "message": "最低提现金额为1元"}
        )
    
    available = current_user.balance - (current_user.frozen_balance or 0)
    if request.amount > available:
        raise HTTPException(
            status_code=400, 
            detail={"code": 20001, "message": "余额不足"}
        )
    
    # TODO: 实际提现逻辑，这里只是示例
    # 实际应该:
    # 1. 创建提现申请记录
    # 2. 冻结对应金额
    # 3. 调用微信/支付宝转账接口
    # 4. 回调处理结果
    
    return ResponseModel(
        message="提现申请已提交，预计1-3个工作日到账",
        data={"amount": request.amount, "channel": request.channel}
    )

