"""
钱包记录模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class WalletRecord(Base):
    """钱包交易记录表"""
    __tablename__ = "wallet_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(32), unique=True, nullable=False, index=True, comment="记录ID")
    user_id = Column(String(32), nullable=False, index=True, comment="用户ID")
    
    # 交易类型: income-收入, withdraw-提现, refund-退款
    type = Column(String(20), nullable=False, comment="交易类型")
    amount = Column(Float, nullable=False, comment="金额")
    
    # 余额
    balance_before = Column(Float, nullable=False, comment="交易前余额")
    balance_after = Column(Float, nullable=False, comment="交易后余额")
    
    # 关联
    order_id = Column(String(32), nullable=True, comment="关联订单ID")
    
    # 备注
    remark = Column(String(255), nullable=True, comment="备注")
    
    # 时间
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

