"""
用户模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), unique=True, nullable=False, index=True, comment="用户ID")
    openid = Column(String(64), unique=True, nullable=False, index=True, comment="微信OpenID")
    unionid = Column(String(64), nullable=True, comment="微信UnionID")
    nickname = Column(String(64), nullable=True, comment="昵称")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    phone = Column(String(20), nullable=True, comment="手机号")
    
    # 实名认证
    real_name = Column(String(32), nullable=True, comment="真实姓名")
    id_card = Column(String(32), nullable=True, comment="身份证号(加密)")
    is_verified = Column(Boolean, default=False, comment="是否实名认证")
    
    # 钱包
    balance = Column(Float, default=0.0, comment="余额")
    frozen_balance = Column(Float, default=0.0, comment="冻结金额")
    points = Column(Integer, default=0, comment="积分")
    
    # 统计
    total_weight = Column(Float, default=0.0, comment="累计投递重量(kg)")
    total_carbon = Column(Float, default=0.0, comment="累计碳减排(kg)")
    total_count = Column(Integer, default=0, comment="累计投递次数")
    
    # 时间
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    
    # 状态
    status = Column(Integer, default=1, comment="状态: 0-禁用, 1-正常")

