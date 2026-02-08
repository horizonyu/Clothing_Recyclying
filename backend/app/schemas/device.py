"""
设备Schema - 按照《4G设备-后台通信协议》定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ===== 小程序端使用的Schema（保持兼容） =====

class DeviceListItem(BaseModel):
    """设备列表项"""
    device_id: str
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    distance: Optional[int] = None


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


# ===== 设备通信协议 Schema =====
# 按照《4G设备-后台通信协议》文档定义
# 报文格式：0x6868 + JSON数据体 + 0x1616
# 校验码：MD5

# --- 上行报文（设备 → 后台）---

class LocationData(BaseModel):
    """位置数据"""
    longitude: float = Field(..., description="经度，保留4位小数")
    latitude: float = Field(..., description="纬度，保留4位小数")
    address: str = Field("", description="地址描述")


class CameraData(BaseModel):
    """摄像头数据"""
    camera_1: List[str] = Field(default_factory=list, description="摄像头1的图片数据（Base64编码），3张")
    camera_2: List[str] = Field(default_factory=list, description="摄像头2的图片数据（Base64编码），3张")


class DeviceStatusData(BaseModel):
    """设备常规状态上报 - 数据体"""
    battery_level: int = Field(..., ge=0, le=100, description="电池电量百分比，0-100")
    location: LocationData = Field(..., description="位置信息")
    smoke_sensor_status: int = Field(..., description="烟感状态：0-正常，1-告警")
    recycle_bin_full: int = Field(..., description="仓体满空：0-未满，1-已满")
    delivery_window_open: int = Field(..., description="投放窗口：0-关闭，1-打开")
    is_using: int = Field(..., description="使用状态：0-无人使用，1-有人使用")
    camera_data: CameraData = Field(default_factory=CameraData, description="摄像头数据，有人使用时必填")


class DeviceStatusReport(BaseModel):
    """设备常规状态上报报文
    
    触发条件：设备烟感状态、仓体满空、投放窗口、使用状态、电量、定位发生变化时立即上报；
    设备被使用时，附加摄像头照片数据。
    """
    msg_type: str = Field("device_status_report", description="报文类型，固定为device_status_report")
    device_id: str = Field(..., description="设备编号")
    timestamp: str = Field(..., description="时间戳，格式为yyyy-MM-dd HH:mm:ss")
    data: DeviceStatusData = Field(..., description="设备状态数据")
    check_code: str = Field(..., description="MD5校验码")


class HeartbeatReport(BaseModel):
    """设备心跳包上报报文
    
    触发条件：设备每8小时定时上报，无状态变化仅上报心跳。
    硬件直接与后台服务通信。
    """
    msg_type: str = Field("heartbeat_report", description="报文类型，固定为heartbeat_report")
    device_id: str = Field(..., description="设备编号")
    timestamp: str = Field(..., description="时间戳，格式为yyyy-MM-dd HH:mm:ss")
    check_code: str = Field(..., description="MD5校验码")


# --- 下行报文（后台 → 设备）---

class TimeSyncData(BaseModel):
    """时间同步数据体"""
    standard_time: str = Field(..., description="后台标准北京时间，格式为yyyy-MM-dd HH:mm:ss")


class TimeSyncResponse(BaseModel):
    """后台时间同步下发报文
    
    触发条件：设备上电首次通信、后台收到设备心跳包后立即下发。
    """
    msg_type: str = Field("time_sync", description="报文类型，固定为time_sync")
    device_id: str = Field(..., description="设备编号")
    timestamp: str = Field(..., description="时间戳")
    data: TimeSyncData = Field(..., description="时间同步数据")
    check_code: str = Field(..., description="MD5校验码")


class ServerAckData(BaseModel):
    """后台应答数据体"""
    reply_msg_type: str = Field(..., description="被应答的报文类型，如device_status_report/heartbeat_report")
    ack_code: int = Field(..., description="0-接收成功，1-接收失败")
    ack_desc: str = Field(..., description="应答结果描述")


class ServerAckResponse(BaseModel):
    """后台应答设备上报报文
    
    触发条件：后台收到设备常规状态上报、心跳上报后，立即回复应答。
    """
    msg_type: str = Field("server_ack", description="报文类型，固定为server_ack")
    device_id: str = Field(..., description="设备编号")
    timestamp: str = Field(..., description="时间戳")
    data: ServerAckData = Field(..., description="应答数据")
    check_code: str = Field(..., description="MD5校验码")


class QueryDeviceStatus(BaseModel):
    """后台主动查询设备状态报文
    
    触发条件：后台运维、业务需要时，主动下发查询指令。
    设备收到后，立即上报全量常规状态。
    """
    msg_type: str = Field("query_device_status", description="报文类型，固定为query_device_status")
    device_id: str = Field(..., description="设备编号")
    timestamp: str = Field(..., description="时间戳")
    check_code: str = Field(..., description="MD5校验码")


# --- 小程序扫码上报的请求 ---

class QrcodeDeviceReportRequest(BaseModel):
    """小程序扫码上报请求
    
    用户投递衣物后，硬件生成二维码（包含device_status_report报文），
    用户扫码后由小程序提取报文内容上报给后台。
    
    二维码内容格式：0x6868 + JSON数据体 + 0x1616
    小程序需要去除包头包尾后，将JSON字符串发送给后台。
    """
    raw_data: str = Field(..., description="二维码扫描得到的原始数据（含或不含包头包尾均可）")
