"""
设备Schema
"""
from pydantic import BaseModel
from typing import Optional


class DeviceListItem(BaseModel):
    """设备列表项"""
    device_id: str
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    distance: Optional[int] = None  # 距离(米)


class DeviceDetailResponse(BaseModel):
    """设备详情响应"""
    device_id: str
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    unit_price: float
    capacity_percent: int

