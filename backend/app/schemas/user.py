"""
用户Schema
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str


class UserLoginResponse(BaseModel):
    """登录响应"""
    token: str
    user_id: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    is_new_user: bool = False


class UserProfileResponse(BaseModel):
    """用户信息响应"""
    user_id: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    is_verified: bool = False
    balance: float = 0.0
    points: int = 0
    total_weight: float = 0.0
    total_carbon: float = 0.0
    total_count: int = 0


class WalletBalanceResponse(BaseModel):
    """钱包余额响应"""
    balance: float
    frozen_balance: float
    available_balance: float
    points: int


class WalletRecordItem(BaseModel):
    """钱包记录项"""
    id: str
    type: str
    amount: float
    created_at: datetime
    remark: Optional[str] = None


class WithdrawRequest(BaseModel):
    """提现请求"""
    amount: float
    channel: str = "wechat"

