"""
设备API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import math

from app.db.database import get_db
from app.models.device import Device
from app.schemas.common import ResponseModel
from app.schemas.device import DeviceListItem, DeviceDetailResponse

router = APIRouter()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """计算两点之间的距离(米)"""
    R = 6371000  # 地球半径(米)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return int(R * c)


@router.get("/nearby", response_model=ResponseModel)
async def get_nearby_devices(
    longitude: float = Query(..., description="经度"),
    latitude: float = Query(..., description="纬度"),
    radius: int = Query(5000, description="搜索半径(米)"),
    db: AsyncSession = Depends(get_db)
):
    """获取附近设备"""
    # 查询所有设备
    result = await db.execute(
        select(Device).where(
            Device.latitude.isnot(None),
            Device.longitude.isnot(None)
        )
    )
    devices = result.scalars().all()
    
    # 计算距离并筛选
    nearby = []
    for device in devices:
        distance = calculate_distance(
            latitude, longitude,
            device.latitude, device.longitude
        )
        if distance <= radius:
            nearby.append({
                "device": device,
                "distance": distance
            })
    
    # 按距离排序
    nearby.sort(key=lambda x: x["distance"])
    
    items = [
        DeviceListItem(
            device_id=item["device"].device_id,
            name=item["device"].name,
            address=item["device"].address,
            latitude=item["device"].latitude,
            longitude=item["device"].longitude,
            status=item["device"].status,
            distance=item["distance"]
        )
        for item in nearby
    ]
    
    return ResponseModel(data=items)


@router.get("/{device_id}/info", response_model=ResponseModel)
async def get_device_info(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取设备详情"""
    result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        return ResponseModel(code=10002, message="设备不存在")
    
    return ResponseModel(data=DeviceDetailResponse(
        device_id=device.device_id,
        name=device.name,
        address=device.address,
        latitude=device.latitude,
        longitude=device.longitude,
        status=device.status,
        unit_price=device.unit_price,
        capacity_percent=device.capacity_percent
    ))


@router.get("/search", response_model=ResponseModel)
async def search_devices(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    db: AsyncSession = Depends(get_db)
):
    """搜索设备"""
    result = await db.execute(
        select(Device).where(
            (Device.name.contains(keyword)) |
            (Device.address.contains(keyword))
        ).limit(20)
    )
    devices = result.scalars().all()
    
    items = [
        DeviceListItem(
            device_id=d.device_id,
            name=d.name,
            address=d.address,
            latitude=d.latitude,
            longitude=d.longitude,
            status=d.status,
            distance=None
        )
        for d in devices
    ]
    
    return ResponseModel(data=items)

