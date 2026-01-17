"""
管理后台 - 设备管理API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.db.database import get_db
from app.models.device import Device
from app.models.admin import Admin
from app.schemas.common import ResponseModel, PaginatedResponse
from app.api.v1.admin import get_current_admin

router = APIRouter()


@router.get("/device/list", response_model=ResponseModel)
async def get_device_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    device_id: str = Query(None),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取设备列表"""
    query = select(Device)
    
    # 筛选条件
    conditions = []
    if device_id:
        conditions.append(Device.device_id.like(f"%{device_id}%"))
    if status:
        conditions.append(Device.status == status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # 分页查询
    query = query.order_by(Device.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    devices = result.scalars().all()
    
    # 转换为字典
    items = []
    for device in devices:
        items.append({
            "device_id": device.device_id,
            "name": device.name,
            "address": device.address,
            "status": device.status,
            "unit_price": device.unit_price,
            "total_orders": 0,  # TODO: 统计订单数
            "total_weight": 0.0  # TODO: 统计重量
        })
    
    return ResponseModel(data=PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))
