"""
设备通信API - 按照《4G设备-后台通信协议》实现

协议概述：
- 采用TCP长连接通信（HTTP接口兼容），数据传输格式为JSON
- 报文格式：包头(0x6868) + JSON数据体 + 校验位(check_code) + 包尾(0x1616)
- 校验算法：MD5

报文类型：
- 上行（设备→后台）：device_status_report（常规状态上报）、heartbeat_report（心跳上报）
- 下行（后台→设备）：server_ack（应答）、time_sync（时间同步）、query_device_status（查询）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import json

from app.db.database import get_db
from app.schemas.common import ResponseModel
from app.schemas.device import (
    DeviceStatusReport,
    HeartbeatReport,
    QrcodeDeviceReportRequest,
    QueryDeviceStatus,
)
from app.services.device_service import (
    DeviceService,
    verify_check_code,
    strip_packet_wrapper,
    build_server_ack,
    build_time_sync,
    build_query_device_status,
    wrap_packet,
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


# ===== 一、设备主动上报接口 =====

@router.post("/report", response_model=ResponseModel)
async def device_status_report(
    report: DeviceStatusReport,
    db: AsyncSession = Depends(get_db)
):
    """
    设备常规状态上报（硬件直接调用）
    
    触发条件：设备烟感状态、仓体满空、投放窗口、使用状态、电量、定位发生变化时立即上报。
    
    报文格式（JSON）：
    ```json
    {
        "msg_type": "device_status_report",
        "device_id": "DEV_202601300001",
        "timestamp": "2026-01-30 10:00:00",
        "data": {
            "battery_level": 85,
            "location": {"longitude": 113.9423, "latitude": 22.5431, "address": "..."},
            "smoke_sensor_status": 0,
            "recycle_bin_full": 0,
            "delivery_window_open": 0,
            "is_using": 0,
            "camera_data": {"camera_1": [], "camera_2": []}
        },
        "check_code": "md5值"
    }
    ```
    
    响应：server_ack 应答报文
    """
    try:
        device_service = DeviceService(db)
        report_dict = report.dict()
        
        success, message, ack = await device_service.process_device_status_report(report_dict)
        
        if success:
            return ResponseModel(
                code=0,
                message="数据接收成功",
                data=ack
            )
        else:
            return ResponseModel(
                code=1,
                message=message,
                data=ack
            )
    except Exception as e:
        logger.error(f"处理设备状态上报异常: {e}", exc_info=True)
        ack = build_server_ack(report.device_id, "device_status_report", 1, f"服务器异常: {str(e)}")
        return ResponseModel(code=1, message=str(e), data=ack)


@router.post("/heartbeat", response_model=ResponseModel)
async def device_heartbeat(
    heartbeat: HeartbeatReport,
    db: AsyncSession = Depends(get_db)
):
    """
    设备心跳包上报（硬件直接调用）
    
    触发条件：设备每8小时定时上报，无状态变化仅上报心跳。
    
    报文格式（JSON）：
    ```json
    {
        "msg_type": "heartbeat_report",
        "device_id": "DEV_202601300001",
        "timestamp": "2026-01-30 10:00:00",
        "check_code": "md5值"
    }
    ```
    
    响应：server_ack 应答报文 + time_sync 时间同步报文
    """
    try:
        device_service = DeviceService(db)
        heartbeat_dict = heartbeat.dict()
        
        success, message, ack, time_sync = await device_service.process_heartbeat_report(heartbeat_dict)
        
        # 心跳响应同时包含应答和时间同步
        response_data = {
            "ack": ack,
            "time_sync": time_sync
        }
        
        if success:
            return ResponseModel(
                code=0,
                message="数据接收成功",
                data=response_data
            )
        else:
            return ResponseModel(
                code=1,
                message=message,
                data=response_data
            )
    except Exception as e:
        logger.error(f"处理心跳上报异常: {e}", exc_info=True)
        ack = build_server_ack(heartbeat.device_id, "heartbeat_report", 1, f"服务器异常: {str(e)}")
        time_sync = build_time_sync(heartbeat.device_id)
        return ResponseModel(code=1, message=str(e), data={"ack": ack, "time_sync": time_sync})


# ===== 二、小程序扫码上报接口 =====

@router.post("/qrcode-report", response_model=ResponseModel)
async def qrcode_device_report(
    request: QrcodeDeviceReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    小程序扫码上报设备状态
    
    流程：
    1. 用户投递衣物完成后，硬件生成包含device_status_report报文的二维码
    2. 用户使用微信扫一扫扫描二维码
    3. 小程序获取二维码数据，发送到本接口
    4. 后台校验check_code，解析关键参数，更新设备状态
    
    二维码内容格式：0x6868{"msg_type":"device_status_report",...,"check_code":"xxx"}0x1616
    
    请求参数：
    - raw_data: 二维码扫描得到的原始数据（含或不含包头包尾均可）
    """
    try:
        raw_data = request.raw_data
        
        # 1. 去除包头包尾
        json_str = strip_packet_wrapper(raw_data)
        
        # 2. 解析JSON
        try:
            report_data = json.loads(json_str)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail={"code": 10006, "message": "二维码数据格式错误，JSON解析失败"}
            )
        
        # 3. 验证msg_type
        msg_type = report_data.get("msg_type")
        if msg_type != "device_status_report":
            raise HTTPException(
                status_code=400,
                detail={"code": 10006, "message": f"报文类型错误，期望device_status_report，收到{msg_type}"}
            )
        
        # 4. 验证校验码
        if not verify_check_code(report_data):
            raise HTTPException(
                status_code=400,
                detail={"code": 10007, "message": "校验码验证失败"}
            )
        
        # 5. 处理设备状态
        device_service = DeviceService(db)
        success, message, ack = await device_service.process_device_status_report(report_data)
        
        if success:
            # 返回设备信息给小程序
            device = await device_service.get_device(report_data["device_id"])
            device_info = {}
            if device:
                device_info = {
                    "device_id": device.device_id,
                    "name": device.name,
                    "address": device.address,
                    "status": device.status,
                    "unit_price": device.unit_price,
                }
            
            return ResponseModel(
                code=0,
                message="上报成功",
                data={
                    "ack": ack,
                    "device_info": device_info,
                    "report_data": report_data.get("data", {})
                }
            )
        else:
            return ResponseModel(
                code=1,
                message=message,
                data={"ack": ack}
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理扫码上报异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": 10000, "message": f"服务器内部错误: {str(e)}"}
        )


# ===== 三、后台下发接口（管理端调用） =====

@router.post("/query-status", response_model=ResponseModel)
async def query_device_status(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    后台主动查询设备状态（生成查询报文）
    
    触发条件：后台运维、业务需要时，主动下发查询指令。
    设备收到后，立即上报全量常规状态。
    
    本接口生成query_device_status报文，可通过TCP下发给设备。
    
    返回：query_device_status报文（含完整包头包尾格式）
    """
    try:
        # 验证设备存在
        device_service = DeviceService(db)
        device = await device_service.get_device(device_id)
        
        if not device:
            raise HTTPException(
                status_code=404,
                detail={"code": 10001, "message": "设备不存在"}
            )
        
        # 构建查询报文
        query_data = build_query_device_status(device_id)
        
        # 构建完整报文（含包头包尾）
        full_packet = wrap_packet(query_data)
        
        return ResponseModel(
            code=0,
            message="查询报文已生成",
            data={
                "query_packet": query_data,
                "full_packet": full_packet
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成查询报文异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": 10000, "message": f"服务器内部错误: {str(e)}"}
        )


@router.post("/time-sync", response_model=ResponseModel)
async def send_time_sync(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    后台主动下发时间同步（生成时间同步报文）
    
    返回：time_sync报文（含完整包头包尾格式）
    """
    try:
        # 验证设备存在
        device_service = DeviceService(db)
        device = await device_service.get_device(device_id)
        
        if not device:
            raise HTTPException(
                status_code=404,
                detail={"code": 10001, "message": "设备不存在"}
            )
        
        # 构建时间同步报文
        sync_data = build_time_sync(device_id)
        
        # 构建完整报文（含包头包尾）
        full_packet = wrap_packet(sync_data)
        
        return ResponseModel(
            code=0,
            message="时间同步报文已生成",
            data={
                "time_sync_packet": sync_data,
                "full_packet": full_packet
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成时间同步报文异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": 10000, "message": f"服务器内部错误: {str(e)}"}
        )
