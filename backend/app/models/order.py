"""
订单模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class DeliveryOrder(Base):
    """投递订单表"""
    __tablename__ = "delivery_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(32), unique=True, nullable=False, index=True, comment="订单ID")
    voucher_id = Column(String(32), unique=True, nullable=False, index=True, comment="投递凭证ID")
    
    # 设备信息
    device_id = Column(String(32), nullable=False, index=True, comment="设备ID")
    device_name = Column(String(100), nullable=True, comment="设备名称(冗余)")
    device_address = Column(String(255), nullable=True, comment="设备地址(冗余)")
    
    # 用户信息(领取时绑定)
    user_id = Column(String(32), nullable=True, index=True, comment="用户ID")
    
    # 投递数据
    weight = Column(Float, nullable=False, comment="重量(kg)")
    unit_price = Column(Float, nullable=False, comment="单价(元/kg)")
    amount = Column(Float, nullable=False, comment="金额(元)")
    
    # 环保数据
    carbon_reduction = Column(Float, default=0.0, comment="碳减排(kg)")
    points_earned = Column(Integer, default=0, comment="获得积分")
    
    # 签名验证
    signature = Column(String(128), nullable=True, comment="数据签名")
    
    # 状态: 0-待领取, 1-已领取, 2-已过期, 3-异常
    status = Column(Integer, default=0, index=True, comment="订单状态")
    
    # 时间
    door_open_time = Column(DateTime, nullable=True, comment="开门时间")
    door_close_time = Column(DateTime, nullable=True, comment="关门时间")
    qrcode_time = Column(DateTime, nullable=True, comment="二维码生成时间")
    qrcode_expire_time = Column(DateTime, nullable=True, comment="二维码过期时间")
    scan_time = Column(DateTime, nullable=True, comment="扫码时间")
    claim_time = Column(DateTime, nullable=True, comment="领取时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 媒体
    image_url = Column(String(500), nullable=True, comment="投递图片")
    video_url = Column(String(500), nullable=True, comment="投递视频")

