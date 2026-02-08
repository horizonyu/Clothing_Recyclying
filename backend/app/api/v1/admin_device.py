"""
管理后台 - 设备管理API
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from loguru import logger
from app.db.database import get_db
from app.models.device import Device
from app.models.order import DeliveryOrder
from app.models.device_camera import DeviceCameraImage
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
    """获取设备列表（含协议上报数据）"""
    try:
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
        
        # 转换为字典，包含协议新增字段
        items = []
        for device in devices:
            # 计算在线状态（24小时内有心跳则为在线）
            is_online = False
            if device.last_heartbeat:
                is_online = (datetime.now() - device.last_heartbeat).total_seconds() < 86400
            
            # 查询该设备的订单统计
            order_stats = await db.execute(
                select(
                    func.count(DeliveryOrder.id),
                    func.coalesce(func.sum(DeliveryOrder.weight), 0)
                ).where(DeliveryOrder.device_id == device.device_id)
            )
            stats_row = order_stats.one()
            total_orders = stats_row[0] or 0
            total_weight = float(stats_row[1] or 0)
            
            items.append({
                "device_id": device.device_id,
                "name": device.name,
                "address": device.address,
                "latitude": device.latitude,
                "longitude": device.longitude,
                "status": device.status if is_online or device.status != "online" else "offline",
                "unit_price": device.unit_price,
                # 协议新增字段
                "battery_level": device.battery_level,
                "smoke_sensor_status": device.smoke_sensor_status or 0,
                "recycle_bin_full": device.recycle_bin_full or 0,
                "delivery_window_open": device.delivery_window_open or 0,
                "is_using": device.is_using or 0,
                "capacity_percent": device.capacity_percent or 0,
                "firmware_version": device.firmware_version,
                "last_heartbeat": device.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S") if device.last_heartbeat else None,
                # 统计数据
                "total_orders": total_orders,
                "total_weight": round(total_weight, 2),
                "created_at": device.created_at.strftime("%Y-%m-%d %H:%M:%S") if device.created_at else None,
            })
        
        return ResponseModel(data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0
        ))
    except Exception as e:
        logger.error(f"获取设备列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取设备列表失败: {str(e)}")


@router.get("/device/detail/{device_id}", response_model=ResponseModel)
async def get_device_detail(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取设备详情（含全部协议字段）"""
    try:
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        # 在线状态判断
        is_online = False
        if device.last_heartbeat:
            is_online = (datetime.now() - device.last_heartbeat).total_seconds() < 86400
        
        # 订单统计
        order_stats = await db.execute(
            select(
                func.count(DeliveryOrder.id),
                func.coalesce(func.sum(DeliveryOrder.weight), 0),
                func.coalesce(func.sum(DeliveryOrder.amount), 0)
            ).where(DeliveryOrder.device_id == device.device_id)
        )
        stats_row = order_stats.one()
        
        # 今日订单统计
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_stats = await db.execute(
            select(
                func.count(DeliveryOrder.id),
                func.coalesce(func.sum(DeliveryOrder.weight), 0)
            ).where(and_(
                DeliveryOrder.device_id == device.device_id,
                DeliveryOrder.created_at >= today_start
            ))
        )
        today_row = today_stats.one()
        
        # 最近7天每日订单数（用于图表）
        daily_orders = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_date = date + timedelta(days=1)
            day_result = await db.execute(
                select(func.count(DeliveryOrder.id)).where(and_(
                    DeliveryOrder.device_id == device.device_id,
                    DeliveryOrder.created_at >= date,
                    DeliveryOrder.created_at < next_date
                ))
            )
            daily_orders.append({
                "date": date.strftime("%m-%d"),
                "count": day_result.scalar() or 0
            })
        
        # 最新一次摄像头图片（按batch_id分组，取最新）
        latest_camera_images = {"camera_1": [], "camera_2": []}
        try:
            # 取最新的一个batch_id
            latest_batch_result = await db.execute(
                select(DeviceCameraImage.batch_id)
                .where(DeviceCameraImage.device_id == device.device_id)
                .order_by(desc(DeviceCameraImage.created_at))
                .limit(1)
            )
            latest_batch_id = latest_batch_result.scalar()
            
            if latest_batch_id:
                # 获取该batch的所有图片
                batch_images_result = await db.execute(
                    select(DeviceCameraImage)
                    .where(and_(
                        DeviceCameraImage.device_id == device.device_id,
                        DeviceCameraImage.batch_id == latest_batch_id
                    ))
                    .order_by(DeviceCameraImage.camera_type, DeviceCameraImage.image_index)
                )
                batch_images = batch_images_result.scalars().all()
                
                for img in batch_images:
                    camera_key = f"camera_{img.camera_type}"
                    if camera_key in latest_camera_images:
                        latest_camera_images[camera_key].append({
                            "id": img.id,
                            "image_data": img.image_data,
                            "image_index": img.image_index,
                            "captured_at": img.captured_at.strftime("%Y-%m-%d %H:%M:%S") if img.captured_at else None,
                        })
        except Exception as cam_err:
            logger.warning(f"获取摄像头图片失败: {cam_err}")
        
        # 摄像头图片总数
        camera_count_result = await db.execute(
            select(func.count(DeviceCameraImage.id))
            .where(DeviceCameraImage.device_id == device.device_id)
        )
        camera_total_count = camera_count_result.scalar() or 0
        
        data = {
            # 基本信息
            "device_id": device.device_id,
            "name": device.name,
            "address": device.address,
            "latitude": device.latitude,
            "longitude": device.longitude,
            "status": device.status if is_online or device.status != "online" else "offline",
            "unit_price": device.unit_price,
            "min_weight": device.min_weight,
            
            # 协议上报数据
            "battery_level": device.battery_level,
            "smoke_sensor_status": device.smoke_sensor_status or 0,
            "recycle_bin_full": device.recycle_bin_full or 0,
            "delivery_window_open": device.delivery_window_open or 0,
            "is_using": device.is_using or 0,
            "capacity_percent": device.capacity_percent or 0,
            "firmware_version": device.firmware_version,
            "last_heartbeat": device.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S") if device.last_heartbeat else None,
            
            # 传感器数据
            "temperature": device.temperature,
            "humidity": device.humidity,
            "smoke_level": device.smoke_level,
            
            # 摄像头图片
            "camera_images": latest_camera_images,
            "camera_total_count": camera_total_count,
            
            # 统计数据
            "total_orders": stats_row[0] or 0,
            "total_weight": round(float(stats_row[1] or 0), 2),
            "total_amount": round(float(stats_row[2] or 0), 2),
            "today_orders": today_row[0] or 0,
            "today_weight": round(float(today_row[1] or 0), 2),
            
            # 图表数据
            "daily_orders": daily_orders,
            
            # 时间
            "created_at": device.created_at.strftime("%Y-%m-%d %H:%M:%S") if device.created_at else None,
            "updated_at": device.updated_at.strftime("%Y-%m-%d %H:%M:%S") if device.updated_at else None,
        }
        
        return ResponseModel(data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取设备详情失败: {str(e)}")


@router.get("/device/stats", response_model=ResponseModel)
async def get_device_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """获取设备统计概览（用于仪表盘）"""
    try:
        # 总设备数
        total_result = await db.execute(select(func.count(Device.id)))
        total = total_result.scalar() or 0
        
        # 在线设备数（24小时内有心跳）
        online_threshold = datetime.now() - timedelta(hours=24)
        online_result = await db.execute(
            select(func.count(Device.id)).where(
                and_(
                    Device.status == "online",
                    Device.last_heartbeat >= online_threshold
                )
            )
        )
        online = online_result.scalar() or 0
        
        # 离线设备数
        offline = total - online
        
        # 告警设备（烟感告警）
        smoke_alert_result = await db.execute(
            select(func.count(Device.id)).where(Device.smoke_sensor_status == 1)
        )
        smoke_alert = smoke_alert_result.scalar() or 0
        
        # 满载设备
        full_result = await db.execute(
            select(func.count(Device.id)).where(Device.recycle_bin_full == 1)
        )
        full_count = full_result.scalar() or 0
        
        # 使用中设备
        using_result = await db.execute(
            select(func.count(Device.id)).where(Device.is_using == 1)
        )
        using_count = using_result.scalar() or 0
        
        # 低电量设备（电量<20%）
        low_battery_result = await db.execute(
            select(func.count(Device.id)).where(
                and_(
                    Device.battery_level != None,
                    Device.battery_level < 20
                )
            )
        )
        low_battery = low_battery_result.scalar() or 0
        
        return ResponseModel(data={
            "total": total,
            "online": online,
            "offline": offline,
            "smoke_alert": smoke_alert,
            "full_count": full_count,
            "using_count": using_count,
            "low_battery": low_battery,
            "online_rate": round(online / total * 100, 1) if total > 0 else 0,
        })
    except Exception as e:
        logger.error(f"获取设备统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取设备统计失败: {str(e)}")


@router.get("/device/{device_id}/camera-images", response_model=ResponseModel)
async def get_device_camera_images(
    device_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    camera_type: int = Query(None, description="摄像头类型: 1-内部, 2-用户"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    获取设备摄像头图片历史记录
    
    按上报批次分组返回，每个批次包含所有摄像头的图片。
    """
    try:
        # 查询不重复的batch_id（按时间倒序）
        batch_query = (
            select(DeviceCameraImage.batch_id)
            .where(DeviceCameraImage.device_id == device_id)
            .group_by(DeviceCameraImage.batch_id)
            .order_by(desc(func.max(DeviceCameraImage.created_at)))
        )
        
        # 总批次数
        count_subquery = batch_query.subquery()
        total_result = await db.execute(select(func.count()).select_from(count_subquery))
        total = total_result.scalar() or 0
        
        # 分页获取batch_id列表
        batch_ids_result = await db.execute(
            batch_query.offset((page - 1) * page_size).limit(page_size)
        )
        batch_ids = [row[0] for row in batch_ids_result.all()]
        
        # 获取这些batch的所有图片
        batches = []
        for bid in batch_ids:
            conditions = [
                DeviceCameraImage.device_id == device_id,
                DeviceCameraImage.batch_id == bid
            ]
            if camera_type is not None:
                conditions.append(DeviceCameraImage.camera_type == camera_type)
            
            images_result = await db.execute(
                select(DeviceCameraImage)
                .where(and_(*conditions))
                .order_by(DeviceCameraImage.camera_type, DeviceCameraImage.image_index)
            )
            images = images_result.scalars().all()
            
            if images:
                batch_data = {
                    "batch_id": bid,
                    "captured_at": images[0].captured_at.strftime("%Y-%m-%d %H:%M:%S") if images[0].captured_at else None,
                    "camera_1": [],
                    "camera_2": [],
                }
                for img in images:
                    camera_key = f"camera_{img.camera_type}"
                    if camera_key in batch_data:
                        batch_data[camera_key].append({
                            "id": img.id,
                            "image_data": img.image_data,
                            "image_index": img.image_index,
                        })
                batches.append(batch_data)
        
        return ResponseModel(data={
            "items": batches,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if total > 0 else 0,
        })
    except Exception as e:
        logger.error(f"获取设备摄像头图片失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取设备摄像头图片失败: {str(e)}")
