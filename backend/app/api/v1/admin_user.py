"""
管理后台 - 用户管理API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger
from app.db.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.schemas.common import ResponseModel, PaginatedResponse
from app.api.v1.admin import get_current_admin

router = APIRouter()


@router.get("/user/list", response_model=ResponseModel)
async def get_user_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Query(None),
    phone: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取用户列表"""
    try:
        query = select(User)
    
    # 筛选条件
    conditions = []
    if user_id:
        conditions.append(User.user_id.like(f"%{user_id}%"))
    if phone:
        conditions.append(User.phone.like(f"%{phone}%"))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # 分页查询
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 转换为字典
    items = []
    for user in users:
        items.append({
            "user_id": user.user_id,
            "nickname": user.nickname,
            "phone": user.phone,
            "balance": user.balance,
            "total_weight": user.total_weight,
            "total_count": user.total_count,
            "is_verified": user.is_verified,
            "status": user.status
        })
    
        return ResponseModel(data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0
        ))
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.put("/user/{user_id}/status", response_model=ResponseModel)
async def update_user_status(
    user_id: str,
    status: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """更新用户状态"""
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user.status = status
        await db.commit()
        
        return ResponseModel(message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新用户状态失败: {str(e)}")
