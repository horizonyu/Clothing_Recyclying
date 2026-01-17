"""
管理后台API
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.db.database import get_db
from app.models.admin import Admin
from app.models.user import User
from app.models.order import DeliveryOrder
from app.models.device import Device
from app.models.withdraw import WithdrawRecord
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminProfileResponse,
    DashboardStatsResponse
)
from app.config import settings
from loguru import logger

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取当前管理员"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    
    result = await db.execute(select(Admin).where(Admin.username == username))
    admin = result.scalar_one_or_none()
    
    if admin is None or admin.status != 1:
        raise HTTPException(status_code=401, detail="管理员不存在或已被禁用")
    
    return admin


@router.post("/auth/login", response_model=ResponseModel)
async def admin_login(
    request: AdminLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """管理员登录"""
    # 查询管理员
    result = await db.execute(select(Admin).where(Admin.username == request.username))
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    if admin.status != 1:
        raise HTTPException(status_code=400, detail="账号已被禁用")
    
    # 验证密码
    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    # 更新最后登录时间
    admin.last_login_at = datetime.now()
    await db.commit()
    
    # 生成token
    access_token = create_access_token(data={"sub": admin.username})
    
    return ResponseModel(data=AdminLoginResponse(
        token=access_token,
        username=admin.username,
        nickname=admin.nickname,
        role=admin.role
    ))


@router.post("/auth/logout", response_model=ResponseModel)
async def admin_logout(
    current_admin: Admin = Depends(get_current_admin)
):
    """退出登录"""
    return ResponseModel(message="退出成功")


@router.get("/auth/profile", response_model=ResponseModel)
async def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin)
):
    """获取管理员信息"""
    import json
    permissions = []
    if current_admin.permissions:
        try:
            permissions = json.loads(current_admin.permissions)
        except:
            pass
    
    return ResponseModel(data=AdminProfileResponse(
        id=current_admin.id,
        username=current_admin.username,
        nickname=current_admin.nickname,
        email=current_admin.email,
        phone=current_admin.phone,
        role=current_admin.role,
        permissions=permissions,
        last_login_at=current_admin.last_login_at
    ))


@router.get("/dashboard/stats", response_model=ResponseModel)
async def get_dashboard_stats(
    period: str = Query("today", description="统计周期: today/7days/30days"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取工作台统计数据"""
    try:
        now = datetime.now()
        
        # 今日开始时间（用于计算今日数据）
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # 昨日开始时间（用于计算趋势）
        yesterday_start = today_start - timedelta(days=1)
        
        # 今日订单数
        today_orders_result = await db.execute(
            select(func.count(DeliveryOrder.id)).where(
                DeliveryOrder.created_at >= today_start
            )
        )
        today_orders = today_orders_result.scalar() or 0
        
        # 今日重量
        today_weight_result = await db.execute(
            select(func.sum(DeliveryOrder.weight)).where(
                DeliveryOrder.created_at >= today_start
            )
        )
        today_weight = float(today_weight_result.scalar() or 0)
        
        # 今日金额
        today_amount_result = await db.execute(
            select(func.sum(DeliveryOrder.amount)).where(
                DeliveryOrder.created_at >= today_start
            )
        )
        today_amount = float(today_amount_result.scalar() or 0)
        
        # 活跃用户（今日有订单的用户）
        active_users_result = await db.execute(
            select(func.count(func.distinct(DeliveryOrder.user_id))).where(
                DeliveryOrder.created_at >= today_start
            )
        )
        active_users = active_users_result.scalar() or 0
        
        # 计算趋势（与昨日对比）
        yesterday_orders_result = await db.execute(
            select(func.count(DeliveryOrder.id)).where(
                and_(
                    DeliveryOrder.created_at >= yesterday_start,
                    DeliveryOrder.created_at < today_start
                )
            )
        )
        yesterday_orders = yesterday_orders_result.scalar() or 0
        
        orders_trend = ((today_orders - yesterday_orders) / yesterday_orders * 100) if yesterday_orders > 0 else 0
        
        # 图表数据（7天）
        chart_dates = []
        chart_values = []
        for i in range(6, -1, -1):
            date = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_date = date + timedelta(days=1)
            chart_dates.append(date.strftime('%m-%d'))
            
            day_orders_result = await db.execute(
                select(func.count(DeliveryOrder.id)).where(
                    and_(
                        DeliveryOrder.created_at >= date,
                        DeliveryOrder.created_at < next_date
                    )
                )
            )
            chart_values.append(day_orders_result.scalar() or 0)
        
        # 告警信息（示例）
        alerts = []
        offline_devices_result = await db.execute(
            select(func.count(Device.id)).where(Device.status == "offline")
        )
        offline_count = offline_devices_result.scalar() or 0
        if offline_count > 0:
            alerts.append({
                "id": 1,
                "level": "警告",
                "message": f"有{offline_count}台设备离线",
                "time": now.strftime('%H:%M')
            })
        
        return ResponseModel(data=DashboardStatsResponse(
            today_orders=today_orders,
            today_weight=round(today_weight, 2),
            today_amount=round(today_amount, 2),
            active_users=active_users,
            orders_trend=round(orders_trend, 1),
            weight_trend=0.0,  # TODO: 计算重量趋势
            amount_trend=0.0,   # TODO: 计算金额趋势
            users_trend=0.0,    # TODO: 计算用户趋势
            chart_data={
                "dates": chart_dates,
                "values": chart_values
            },
            alerts=alerts
        ))
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}", exc_info=True)
        # 返回空数据，避免前端报错
        return ResponseModel(data=DashboardStatsResponse(
            today_orders=0,
            today_weight=0.0,
            today_amount=0.0,
            active_users=0,
            orders_trend=0.0,
            weight_trend=0.0,
            amount_trend=0.0,
            users_trend=0.0,
            chart_data={
                "dates": [],
                "values": []
            },
            alerts=[]
        ))
