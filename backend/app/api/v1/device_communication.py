"""
设备通信API - 按照《4G设备-后台通信协议》实现

协议概述：
- 支持 WebSocket 长连接 和 HTTP 短连接两种通信方式
- 数据传输格式为JSON
- 报文格式：包头(0x6868) + JSON数据体 + 校验位(check_code) + 包尾(0x1616)
- 校验算法：MD5

通信方式（优先级从高到低）：
1. WebSocket 长连接 ws://server/api/v1/device/ws/{device_id}（推荐）
   - 设备与后台建立持久双向连接，心跳/状态上报/命令接收全部走同一通道
2. HTTP 长轮询 GET /device/listen/{device_id}（兼容）
   - 设备周期性发起长轮询请求，等待后台命令推送
3. HTTP 短连接 POST /device/report, /device/heartbeat（兜底）
   - 传统请求-响应模式

报文类型：
- 上行（设备→后台）：device_status_report（常规状态上报）、heartbeat_report（心跳上报）
- 下行（后台→设备）：server_ack（应答）、time_sync（时间同步）、query_device_status（查询）
"""
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import json

from app.db.database import get_db, AsyncSessionLocal
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
    connection_manager,
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
        
        success, message, ack, time_sync = await device_service.process_device_status_report(report_dict)
        
        # 构建响应数据
        response_data = {"ack": ack}
        
        # 按协议：设备首次上报数据时（从未向后台上报过），
        # 除了返回ack消息，还需返回time_sync消息
        if time_sync:
            response_data["time_sync"] = time_sync
        
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
        logger.error(f"处理设备状态上报异常: {e}", exc_info=True)
        ack = build_server_ack(report.device_id, "device_status_report", 1, f"服务器异常: {str(e)}")
        return ResponseModel(code=1, message=str(e), data={"ack": ack})


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
        
        success, message, ack, time_sync, pending_cmd = await device_service.process_heartbeat_report(heartbeat_dict)
        
        # 心跳响应同时包含应答和时间同步
        response_data = {
            "ack": ack,
            "time_sync": time_sync
        }
        
        # 如果有待执行命令，一并下发（如 query_device_status）
        if pending_cmd:
            response_data["command"] = pending_cmd
        
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
        success, message, ack, _time_sync = await device_service.process_device_status_report(report_data)
        
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


# ===== 三、设备 WebSocket 长连接 =====

@router.websocket("/ws/{device_id}")
async def device_websocket(websocket: WebSocket, device_id: str):
    """
    设备 WebSocket 统一通信端点（推荐使用）
    
    建立持久双向长连接。设备连接后，所有上行（心跳、状态上报）和
    下行（应答、时间同步、查询命令）消息都通过此连接传输。
    
    上行消息（设备→后台）：
    - heartbeat_report  — 心跳包（建议每8小时一次，保活可更频繁）
    - device_status_report — 状态上报（含传感器和摄像头数据）
    
    下行消息（后台→设备）：
    - server_ack — 应答
    - time_sync — 时间同步
    - query_device_status — 后台主动查询指令（实时推送）
    
    消息格式：
    - 设备发送纯 JSON 文本，或带包头包尾的报文（0x6868{JSON}0x1616）
    - 后台回复纯 JSON 对象
    
    连接断开时自动标记设备为离线。
    """
    await websocket.accept()
    await connection_manager.ws_connect(device_id, websocket)
    
    # 上线处理
    try:
        async with AsyncSessionLocal() as db:
            device_service = DeviceService(db)
            device = await device_service.get_device(device_id)
            if device:
                device.status = "online"
                device.last_heartbeat = datetime.now()
                await db.commit()
                logger.info(f"[WS] 设备 {device_id} 上线")
            else:
                logger.warning(f"[WS] 未注册设备 {device_id} 尝试连接")
    except Exception as e:
        logger.error(f"[WS] 设备 {device_id} 上线处理异常: {e}")
    
    try:
        while True:
            raw_text = await websocket.receive_text()
            
            # 解析消息（支持带/不带包头包尾）
            try:
                json_str = strip_packet_wrapper(raw_text) if raw_text.startswith("0x6868") else raw_text
                data = json.loads(json_str)
            except (json.JSONDecodeError, Exception) as e:
                err_ack = build_server_ack(device_id, "unknown", 1, f"消息格式错误: {str(e)}")
                await websocket.send_json(err_ack)
                continue
            
            msg_type = data.get("msg_type", "")
            logger.debug(f"[WS] 设备 {device_id} 收到消息: {msg_type}")
            
            # 每条消息使用独立的数据库会话
            try:
                async with AsyncSessionLocal() as db:
                    device_service = DeviceService(db)
                    
                    if msg_type == "heartbeat_report":
                        success, message, ack, time_sync, pending_cmd = \
                            await device_service.process_heartbeat_report(data)
                        await websocket.send_json(ack)
                        await websocket.send_json(time_sync)
                        if pending_cmd:
                            await websocket.send_json(pending_cmd)
                    
                    elif msg_type == "device_status_report":
                        success, message, ack, time_sync = \
                            await device_service.process_device_status_report(data)
                        await websocket.send_json(ack)
                        if time_sync:
                            await websocket.send_json(time_sync)
                    
                    else:
                        err_ack = build_server_ack(device_id, msg_type, 1, f"未知消息类型: {msg_type}")
                        await websocket.send_json(err_ack)
            except Exception as e:
                logger.error(f"[WS] 处理设备 {device_id} 消息 {msg_type} 异常: {e}", exc_info=True)
                err_ack = build_server_ack(device_id, msg_type, 1, f"处理异常: {str(e)}")
                try:
                    await websocket.send_json(err_ack)
                except Exception:
                    break
    
    except WebSocketDisconnect:
        logger.info(f"[WS] 设备 {device_id} 正常断开连接")
    except Exception as e:
        logger.error(f"[WS] 设备 {device_id} 连接异常: {e}", exc_info=True)
    finally:
        connection_manager.ws_disconnect(device_id)
        # 离线处理
        try:
            async with AsyncSessionLocal() as db:
                device_service = DeviceService(db)
                device = await device_service.get_device(device_id)
                if device:
                    device.status = "offline"
                    await db.commit()
                    logger.info(f"[WS] 设备 {device_id} 已标记为离线")
        except Exception as e:
            logger.error(f"[WS] 设备 {device_id} 离线处理异常: {e}")


# ===== 四、设备长轮询监听接口（向下兼容） =====

@router.get("/listen/{device_id}", response_model=ResponseModel)
async def device_listen(
    device_id: str,
    timeout: int = Query(60, ge=5, le=120, description="长轮询超时时间(秒)")
):
    """
    设备长轮询监听命令（向下兼容，推荐使用 WebSocket 接口）
    
    如果设备不支持 WebSocket，可使用此接口保持监听。
    设备启动后应持续调用此接口。当后台管理员下发命令时，
    命令会通过此连接实时推送到设备。
    
    工作流程：
    1. 设备调用此接口，连接保持挂起状态（最长 timeout 秒）
    2. 如果后台有命令下发 → 立即返回命令报文，设备收到后执行
    3. 如果超时无命令 → 返回空响应，设备应立即重新连接
    
    参数：
    - device_id: 设备编号
    - timeout: 长轮询超时时间，默认60秒，范围5~120秒
    """
    channel = connection_manager.get_lp_channel(device_id)
    logger.info(f"[LP] 设备 {device_id} 开始长轮询监听 (timeout={timeout}s)")
    
    try:
        # 阻塞等待命令，超时则返回空
        command = await asyncio.wait_for(channel.get(), timeout=timeout)
        
        full_packet = wrap_packet(command)
        logger.info(f"[LP] 向设备 {device_id} 下发命令: {command.get('msg_type', 'unknown')}")
        
        return ResponseModel(
            code=0,
            message="收到命令，请立即执行",
            data={
                "has_command": True,
                "command": command,
                "full_packet": full_packet
            }
        )
    except asyncio.TimeoutError:
        return ResponseModel(
            code=0,
            message="无待执行命令",
            data={
                "has_command": False
            }
        )
    except Exception as e:
        logger.error(f"[LP] 设备 {device_id} 监听异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": 10000, "message": f"服务器内部错误: {str(e)}"}
        )
    finally:
        pass


# ===== 五、后台下发接口（管理端调用） =====

@router.post("/query-status", response_model=ResponseModel)
async def query_device_status(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    后台主动查询设备状态（实时下发）
    
    触发条件：后台运维、业务需要时，主动下发查询指令。
    设备收到后，立即采集并上报全量常规状态（device_status_report），
    后台通过 /report 接口（或 WebSocket）接收并更新设备信息。
    
    命令下发优先级：
    1. WebSocket 长连接 → 直接推送，设备立即收到
    2. HTTP 长轮询 → 推入 Queue，设备长轮询立即返回
    3. 数据库排队 → 写入 pending_command，设备下次心跳时获取
    
    返回：query_device_status 报文 + 下发方式（websocket/long_polling/queued）
    """
    try:
        device_service = DeviceService(db)
        
        # 使用 send_command 方法：优先实时推送，离线回退排队
        success, delivery_method = await device_service.send_command(device_id, "query_device_status")
        
        if not success:
            if delivery_method == "device_not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": 10001, "message": "设备不存在"}
                )
            raise HTTPException(status_code=500, detail="命令发送失败")
        
        query_data = build_query_device_status(device_id)
        full_packet = wrap_packet(query_data)
        
        method_info = {
            "websocket": ("查询命令已通过 WebSocket 实时下发到设备", "WebSocket 实时推送"),
            "long_polling": ("查询命令已通过长轮询实时下发到设备", "长轮询实时推送"),
            "queued": ("设备当前不在线，命令已排队，设备上线后将自动获取", "排队等待（设备离线）"),
        }
        message, delivery_desc = method_info.get(
            delivery_method, ("命令已发送", delivery_method)
        )
        
        logger.info(f"查询设备 {device_id} 状态: {delivery_desc}")
        
        return ResponseModel(
            code=0,
            message=message,
            data={
                "query_packet": query_data,
                "full_packet": full_packet,
                "delivery_method": delivery_method,
                "delivery_desc": delivery_desc,
                "device_online": delivery_method in ("websocket", "long_polling")
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询设备状态异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": 10000, "message": f"服务器内部错误: {str(e)}"}
        )


@router.get("/pending-commands/{device_id}", response_model=ResponseModel)
async def get_pending_commands(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    设备轮询待执行命令（硬件直接调用 —— 向下兼容）
    
    注意：推荐使用 GET /device/listen/{device_id} 长轮询接口替代本接口。
    长轮询接口支持实时命令推送，无需定期轮询。
    
    本接口仅作为回退方案，用于不支持长轮询的设备。
    如果有待执行命令（如 query_device_status），将返回命令报文。
    命令获取后会自动清除，不会重复下发。
    """
    try:
        device_service = DeviceService(db)
        cmd_packet = await device_service.get_and_clear_pending_command(device_id)
        
        if cmd_packet:
            full_packet = wrap_packet(cmd_packet)
            return ResponseModel(
                code=0,
                message="有待执行命令",
                data={
                    "has_command": True,
                    "command": cmd_packet,
                    "full_packet": full_packet
                }
            )
        else:
            return ResponseModel(
                code=0,
                message="无待执行命令",
                data={
                    "has_command": False
                }
            )
    except Exception as e:
        logger.error(f"获取待执行命令异常: {e}", exc_info=True)
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
