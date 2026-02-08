"""
设备服务层 - 按照《4G设备-后台通信协议》实现
"""
import hashlib
import json
import uuid
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.device import Device
from app.models.device_camera import DeviceCameraImage
from app.schemas.device import (
    DeviceStatusReport,
    HeartbeatReport,
    ServerAckResponse,
    ServerAckData,
    TimeSyncResponse,
    TimeSyncData,
    QueryDeviceStatus,
)

# 报文包头包尾
PACKET_HEADER = "0x6868"
PACKET_FOOTER = "0x1616"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_current_timestamp_str() -> str:
    """获取当前时间的标准格式字符串"""
    return datetime.now().strftime(TIMESTAMP_FORMAT)


def calculate_check_code(packet_data: dict) -> str:
    """
    计算MD5校验码
    
    校验规则（按协议文档）：
    1. 校验范围：包头 + JSON数据体中除check_code外的所有字段拼接字符串
    2. 校验算法：采用MD5加密，生成32位小写字符串
    """
    # 复制数据，去除check_code字段
    data_copy = {k: v for k, v in packet_data.items() if k != "check_code"}
    
    # 将数据序列化为JSON字符串（紧凑格式）
    json_str = json.dumps(data_copy, ensure_ascii=False, separators=(',', ':'))
    
    # 拼接包头 + JSON字符串
    check_str = PACKET_HEADER + json_str
    
    # 计算MD5
    md5_hash = hashlib.md5(check_str.encode('utf-8')).hexdigest()
    
    return md5_hash


def verify_check_code(packet_data: dict) -> bool:
    """
    验证报文校验码
    
    Args:
        packet_data: 报文数据（包含check_code字段）
    
    Returns:
        校验是否通过
    """
    received_check_code = packet_data.get("check_code", "")
    expected_check_code = calculate_check_code(packet_data)
    
    is_valid = received_check_code == expected_check_code
    if not is_valid:
        logger.warning(
            f"校验码验证失败: 期望={expected_check_code}, 收到={received_check_code}"
        )
    
    return is_valid


def strip_packet_wrapper(raw_data: str) -> str:
    """
    去除报文包头包尾，提取JSON数据体
    
    报文格式：0x6868 + JSON数据体 + 0x1616
    """
    data = raw_data.strip()
    
    # 去除包头
    if data.startswith(PACKET_HEADER):
        data = data[len(PACKET_HEADER):]
    
    # 去除包尾
    if data.endswith(PACKET_FOOTER):
        data = data[:-len(PACKET_FOOTER)]
    
    return data.strip()


def wrap_packet(packet_data: dict) -> str:
    """
    添加报文包头包尾
    
    Returns:
        完整报文字符串：0x6868 + JSON + 0x1616
    """
    json_str = json.dumps(packet_data, ensure_ascii=False, separators=(',', ':'))
    return f"{PACKET_HEADER}{json_str}{PACKET_FOOTER}"


def build_server_ack(device_id: str, reply_msg_type: str, ack_code: int, ack_desc: str) -> dict:
    """
    构建后台应答报文
    
    Args:
        device_id: 设备编号
        reply_msg_type: 被应答的报文类型
        ack_code: 0-接收成功，1-接收失败
        ack_desc: 应答描述
    
    Returns:
        应答报文字典（含check_code）
    """
    timestamp = get_current_timestamp_str()
    
    ack_data = {
        "msg_type": "server_ack",
        "device_id": device_id,
        "timestamp": timestamp,
        "data": {
            "reply_msg_type": reply_msg_type,
            "ack_code": ack_code,
            "ack_desc": ack_desc
        }
    }
    
    # 计算校验码
    ack_data["check_code"] = calculate_check_code(ack_data)
    
    return ack_data


def build_time_sync(device_id: str) -> dict:
    """
    构建时间同步下发报文
    
    Args:
        device_id: 设备编号
    
    Returns:
        时间同步报文字典（含check_code）
    """
    timestamp = get_current_timestamp_str()
    
    sync_data = {
        "msg_type": "time_sync",
        "device_id": device_id,
        "timestamp": timestamp,
        "data": {
            "standard_time": timestamp
        }
    }
    
    # 计算校验码
    sync_data["check_code"] = calculate_check_code(sync_data)
    
    return sync_data


def build_query_device_status(device_id: str) -> dict:
    """
    构建后台主动查询设备状态报文
    
    Args:
        device_id: 设备编号
    
    Returns:
        查询报文字典（含check_code）
    """
    timestamp = get_current_timestamp_str()
    
    query_data = {
        "msg_type": "query_device_status",
        "device_id": device_id,
        "timestamp": timestamp
    }
    
    # 计算校验码
    query_data["check_code"] = calculate_check_code(query_data)
    
    return query_data


class DeviceService:
    """设备服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_device(self, device_id: str) -> Optional[Device]:
        """根据设备ID获取设备"""
        result = await self.db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        return result.scalar_one_or_none()
    
    async def process_device_status_report(self, report_data: dict) -> Tuple[bool, str, dict, Optional[dict]]:
        """
        处理设备常规状态上报
        
        按协议规定：设备第一次被用户使用时（is_using=1），
        除了返回ack消息，还需返回time_sync消息。
        
        Args:
            report_data: 设备状态上报报文（JSON字典）
        
        Returns:
            (success, message, ack_response, time_sync_or_none)
        """
        device_id = report_data.get("device_id", "")
        
        try:
            # 1. 验证校验码
            if not verify_check_code(report_data):
                ack = build_server_ack(device_id, "device_status_report", 1, "校验失败")
                return False, "校验码验证失败", ack, None
            
            # 2. 查询设备
            device = await self.get_device(device_id)
            if not device:
                ack = build_server_ack(device_id, "device_status_report", 1, "设备不存在")
                return False, "设备不存在或未注册", ack, None
            
            # 记录之前的使用状态，用于判断是否需要下发time_sync
            previous_is_using = device.is_using or 0
            
            # 3. 更新设备状态
            data = report_data.get("data", {})
            
            device.status = "online"
            device.last_heartbeat = datetime.now()
            
            # 电池电量
            battery_level = data.get("battery_level")
            if battery_level is not None:
                device.battery_level = battery_level
            
            # 位置信息
            location = data.get("location", {})
            if location.get("longitude"):
                device.longitude = location["longitude"]
            if location.get("latitude"):
                device.latitude = location["latitude"]
            if location.get("address"):
                device.address = location["address"]
            
            # 烟感状态
            smoke_sensor_status = data.get("smoke_sensor_status", 0)
            device.smoke_sensor_status = smoke_sensor_status
            device.smoke_level = float(smoke_sensor_status)
            
            # 仓体满空
            recycle_bin_full = data.get("recycle_bin_full", 0)
            device.recycle_bin_full = recycle_bin_full
            device.capacity_percent = 100 if recycle_bin_full == 1 else device.capacity_percent
            
            # 投放窗口
            delivery_window_open = data.get("delivery_window_open", 0)
            device.delivery_window_open = delivery_window_open
            
            # 使用状态
            is_using = data.get("is_using", 0)
            device.is_using = is_using
            
            # 保存摄像头图片数据
            camera_data = data.get("camera_data", {})
            saved_images = 0
            if camera_data:
                batch_id = uuid.uuid4().hex[:16]
                captured_at = datetime.now()
                
                # camera_1: 回收箱内部摄像头
                camera_1_images = camera_data.get("camera_1", [])
                for idx, img_base64 in enumerate(camera_1_images):
                    if img_base64 and len(img_base64) > 10:  # 过滤空数据
                        img_record = DeviceCameraImage(
                            device_id=device_id,
                            camera_type=1,
                            image_index=idx,
                            image_data=img_base64,
                            batch_id=batch_id,
                            captured_at=captured_at,
                        )
                        self.db.add(img_record)
                        saved_images += 1
                
                # camera_2: 用户摄像头
                camera_2_images = camera_data.get("camera_2", [])
                for idx, img_base64 in enumerate(camera_2_images):
                    if img_base64 and len(img_base64) > 10:  # 过滤空数据
                        img_record = DeviceCameraImage(
                            device_id=device_id,
                            camera_type=2,
                            image_index=idx,
                            image_data=img_base64,
                            batch_id=batch_id,
                            captured_at=captured_at,
                        )
                        self.db.add(img_record)
                        saved_images += 1
            
            await self.db.commit()
            
            logger.info(
                f"设备 {device_id} 状态上报处理成功: "
                f"电量={battery_level}%, 烟感={smoke_sensor_status}, "
                f"仓满={recycle_bin_full}, 投放窗口={'开' if delivery_window_open else '关'}, "
                f"使用中={'是' if is_using else '否'}, "
                f"保存图片={saved_images}张"
            )
            
            # 4. 构建成功应答
            ack = build_server_ack(device_id, "device_status_report", 0, "数据接收成功")
            
            # 5. 按协议：设备首次被用户使用时(is_using从0变为1)，
            #    除了返回ack消息，还需返回time_sync消息
            time_sync = None
            if is_using == 1 and previous_is_using == 0:
                time_sync = build_time_sync(device_id)
                logger.info(f"设备 {device_id} 首次被用户使用，下发时间同步")
            
            return True, "处理成功", ack, time_sync
            
        except Exception as e:
            logger.error(f"处理设备状态上报失败: {e}", exc_info=True)
            await self.db.rollback()
            ack = build_server_ack(device_id, "device_status_report", 1, f"处理失败: {str(e)}")
            return False, str(e), ack, None
    
    async def process_heartbeat_report(self, report_data: dict) -> Tuple[bool, str, dict, dict, Optional[dict]]:
        """
        处理设备心跳包上报
        
        按协议规定：收到心跳后下发 time_sync 消息。
        同时检查是否有待执行命令（如 query_device_status），一并下发。
        
        Args:
            report_data: 心跳报文（JSON字典）
        
        Returns:
            (success, message, ack_response, time_sync_response, pending_command_or_none)
        """
        device_id = report_data.get("device_id", "")
        
        try:
            # 1. 验证校验码
            if not verify_check_code(report_data):
                ack = build_server_ack(device_id, "heartbeat_report", 1, "校验失败")
                time_sync = build_time_sync(device_id)
                return False, "校验码验证失败", ack, time_sync, None
            
            # 2. 查询设备
            device = await self.get_device(device_id)
            if not device:
                ack = build_server_ack(device_id, "heartbeat_report", 1, "设备不存在")
                time_sync = build_time_sync(device_id)
                return False, "设备不存在或未注册", ack, time_sync, None
            
            # 3. 更新设备心跳时间
            device.status = "online"
            device.last_heartbeat = datetime.now()
            
            # 4. 检查并获取待执行命令
            pending_cmd_packet = None
            if device.pending_command:
                cmd_type = device.pending_command
                logger.info(f"设备 {device_id} 有待执行命令: {cmd_type}")
                
                if cmd_type == "query_device_status":
                    pending_cmd_packet = build_query_device_status(device_id)
                    logger.info(f"通过心跳响应下发 query_device_status 命令给设备 {device_id}")
                
                # 清除已下发的命令
                device.pending_command = None
                device.pending_command_at = None
            
            await self.db.commit()
            
            logger.info(f"设备 {device_id} 心跳上报处理成功, 时间戳: {report_data.get('timestamp')}")
            
            # 5. 构建应答 + 时间同步
            ack = build_server_ack(device_id, "heartbeat_report", 0, "数据接收成功")
            time_sync = build_time_sync(device_id)
            
            return True, "处理成功", ack, time_sync, pending_cmd_packet
            
        except Exception as e:
            logger.error(f"处理心跳上报失败: {e}", exc_info=True)
            await self.db.rollback()
            ack = build_server_ack(device_id, "heartbeat_report", 1, f"处理失败: {str(e)}")
            time_sync = build_time_sync(device_id)
            return False, str(e), ack, time_sync, None
    
    async def queue_command(self, device_id: str, command: str) -> bool:
        """
        为设备排队一个待执行命令
        
        设备将在下次心跳上报或主动轮询时获取该命令。
        
        Args:
            device_id: 设备ID
            command: 命令类型，如 "query_device_status"
        
        Returns:
            是否成功排队
        """
        device = await self.get_device(device_id)
        if not device:
            return False
        
        device.pending_command = command
        device.pending_command_at = datetime.now()
        await self.db.commit()
        
        logger.info(f"为设备 {device_id} 排队命令: {command}")
        return True
    
    async def get_and_clear_pending_command(self, device_id: str) -> Optional[dict]:
        """
        获取并清除设备的待执行命令（设备主动轮询时使用）
        
        Args:
            device_id: 设备ID
        
        Returns:
            待执行命令报文，如果没有则返回 None
        """
        device = await self.get_device(device_id)
        if not device or not device.pending_command:
            return None
        
        cmd_type = device.pending_command
        cmd_packet = None
        
        if cmd_type == "query_device_status":
            cmd_packet = build_query_device_status(device_id)
        
        # 清除已取走的命令
        device.pending_command = None
        device.pending_command_at = None
        await self.db.commit()
        
        logger.info(f"设备 {device_id} 轮询获取命令: {cmd_type}")
        return cmd_packet
