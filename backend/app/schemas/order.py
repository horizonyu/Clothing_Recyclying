"""
订单Schema
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScanQrcodeRequest(BaseModel):
    """扫码请求"""
    qrcode_data: str


class ScanQrcodeResponse(BaseModel):
    """扫码响应"""
    order_id: str
    voucher_id: str
    device_id: str
    device_name: str
    weight: float
    unit_price: float
    amount: float
    carbon_reduction: float
    points: int
    status: int
    qrcode_time: Optional[datetime] = None
    expire_time: Optional[datetime] = None


class ClaimOrderResponse(BaseModel):
    """领取响应"""
    order_id: str
    amount: float
    weight: float
    carbon_reduction: float
    points_earned: int
    wallet_balance: float


class OrderListItem(BaseModel):
    """订单列表项"""
    order_id: str
    device_name: str
    weight: float
    amount: float
    carbon_reduction: float
    status: int
    created_at: datetime


class OrderDetailResponse(BaseModel):
    """订单详情响应"""
    order_id: str
    voucher_id: str
    device_id: str
    device_name: str
    device_address: Optional[str] = None
    weight: float
    unit_price: float
    amount: float
    carbon_reduction: float
    points_earned: int
    status: int
    created_at: datetime
    claim_time: Optional[datetime] = None


class OrderStatsResponse(BaseModel):
    """订单统计响应"""
    total_count: int
    total_weight: float
    total_amount: float
    total_carbon: float

