"""
提现记录模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class WithdrawStatus(enum.Enum):
    """提现状态"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class WithdrawRecord(Base):
    """提现记录表"""
    __tablename__ = "withdraw_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    withdraw_id = Column(String(32), unique=True, nullable=False, index=True, comment="提现ID")
    user_id = Column(String(32), nullable=False, index=True, comment="用户ID")
    
    # 提现金额
    amount = Column(Float, nullable=False, comment="提现金额(元)")
    
    # 提现渠道
    channel = Column(String(20), nullable=False, comment="提现渠道: wechat/alipay")
    
    # 状态
    status = Column(String(20), nullable=False, default=WithdrawStatus.PENDING.value, comment="提现状态")
    
    # 微信转账信息
    wechat_batch_id = Column(String(64), nullable=True, comment="微信批次单号")
    wechat_detail_id = Column(String(64), nullable=True, comment="微信明细单号")
    wechat_openid = Column(String(64), nullable=True, comment="微信OpenID")
    
    # 错误信息
    error_code = Column(String(32), nullable=True, comment="错误代码")
    error_message = Column(String(255), nullable=True, comment="错误信息")
    
    # 备注
    remark = Column(String(255), nullable=True, comment="备注")
    
    # 时间
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
