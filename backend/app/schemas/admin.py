"""
管理员Schema
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """登录响应"""
    token: str
    username: str
    nickname: Optional[str] = None
    role: str = "admin"


class AdminProfileResponse(BaseModel):
    """管理员信息响应"""
    id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    permissions: Optional[List[str]] = []
    last_login_at: Optional[datetime] = None


class DashboardStatsResponse(BaseModel):
    """工作台统计数据"""
    today_orders: int = 0
    today_weight: float = 0.0
    today_amount: float = 0.0
    active_users: int = 0
    orders_trend: float = 0.0
    weight_trend: float = 0.0
    amount_trend: float = 0.0
    users_trend: float = 0.0
    chart_data: Optional[dict] = None
    alerts: Optional[List[dict]] = []
