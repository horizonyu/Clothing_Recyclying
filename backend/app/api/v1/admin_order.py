"""
管理后台 - 订单管理API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.db.database import get_db
from app.models.order import DeliveryOrder
from app.models.admin import Admin
from app.schemas.common import ResponseModel, PaginatedResponse
from app.api.v1.admin import get_current_admin

router = APIRouter()


@router.get("/order/list", response_model=ResponseModel)
async def get_order_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_id: str = Query(None),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取订单列表"""
    query = select(DeliveryOrder)
    
    # 筛选条件
    conditions = []
    if order_id:
        conditions.append(DeliveryOrder.order_id.like(f"%{order_id}%"))
    if status:
        conditions.append(DeliveryOrder.status == status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # 分页查询
    query = query.order_by(DeliveryOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # 转换为字典
    items = []
    for order in orders:
        items.append({
            "order_id": order.order_id,
            "user_id": order.user_id,
            "device_id": order.device_id,
            "weight": order.weight,
            "amount": order.amount,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None
        })
    
    return ResponseModel(data=PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))
