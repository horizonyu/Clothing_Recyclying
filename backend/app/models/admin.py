"""
管理员模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.database import Base


class Admin(Base):
    """管理员表"""
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(64), nullable=True, comment="昵称")
    email = Column(String(128), nullable=True, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="手机号")
    
    # 角色和权限
    role = Column(String(32), default="admin", comment="角色: super_admin/admin/operator")
    permissions = Column(String(500), nullable=True, comment="权限列表(JSON)")
    
    # 状态
    status = Column(Integer, default=1, comment="状态: 0-禁用, 1-正常")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP")
    
    # 时间
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
