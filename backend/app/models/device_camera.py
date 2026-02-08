"""
设备摄像头图片模型

存储设备上报的摄像头图片数据。
- camera_1: 回收箱内部摄像头（拍摄回收物品）
- camera_2: 外部摄像头（拍摄用户）
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base


class DeviceCameraImage(Base):
    """设备摄像头图片表"""
    __tablename__ = "device_camera_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(32), nullable=False, index=True, comment="设备ID")
    
    # 摄像头类型: 1-回收箱内部摄像头, 2-用户摄像头
    camera_type = Column(Integer, nullable=False, comment="摄像头类型: 1-内部, 2-用户")
    
    # 图片索引（同一次上报可能有多张图片）
    image_index = Column(Integer, default=0, comment="图片序号(同一次上报中)")
    
    # Base64编码的图片数据
    image_data = Column(Text, nullable=False, comment="Base64编码图片数据")
    
    # 上报批次ID（同一次状态上报的所有图片共享一个batch_id）
    batch_id = Column(String(64), nullable=True, index=True, comment="上报批次ID")
    
    # 时间
    captured_at = Column(DateTime, server_default=func.now(), comment="拍摄时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
