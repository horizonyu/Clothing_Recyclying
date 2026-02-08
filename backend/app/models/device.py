"""
设备模型 - 按照《4G设备-后台通信协议》扩展
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.database import Base


class Device(Base):
    """设备表"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(32), unique=True, nullable=False, index=True, comment="设备ID，如DEV_202601300001")
    name = Column(String(100), nullable=False, comment="设备名称")
    address = Column(String(255), nullable=True, comment="设备地址")
    
    # 位置
    latitude = Column(Float, nullable=True, comment="纬度")
    longitude = Column(Float, nullable=True, comment="经度")
    
    # 配置
    device_secret = Column(String(64), nullable=False, comment="设备密钥")
    unit_price = Column(Float, default=0.30, comment="回收单价(元/kg)")
    min_weight = Column(Float, default=0.1, comment="最小称重(kg)")
    
    # 状态
    status = Column(String(20), default="offline", comment="状态: online/offline/maintenance")
    last_heartbeat = Column(DateTime, nullable=True, comment="最后心跳时间")
    
    # 容量
    capacity_percent = Column(Integer, default=0, comment="容量百分比")
    current_weight = Column(Float, default=0.0, comment="当前重量(kg)")
    
    # 协议扩展字段（来自设备常规状态上报）
    battery_level = Column(Integer, nullable=True, comment="电池电量百分比(0-100)")
    smoke_sensor_status = Column(Integer, default=0, comment="烟感状态: 0-正常, 1-告警")
    recycle_bin_full = Column(Integer, default=0, comment="仓体满空: 0-未满, 1-已满")
    delivery_window_open = Column(Integer, default=0, comment="投放窗口: 0-关闭, 1-打开")
    is_using = Column(Integer, default=0, comment="使用状态: 0-无人使用, 1-有人使用")
    firmware_version = Column(String(32), nullable=True, comment="固件版本")
    
    # 传感器数据（兼容旧字段）
    temperature = Column(Float, nullable=True, comment="温度")
    humidity = Column(Float, nullable=True, comment="湿度")
    smoke_level = Column(Float, nullable=True, comment="烟雾浓度")
    
    # 时间
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

