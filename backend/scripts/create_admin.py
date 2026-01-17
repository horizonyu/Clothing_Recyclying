"""
创建管理员账号脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from app.models.admin import Admin
from app.api.v1.admin import get_password_hash


async def create_admin():
    """创建管理员账号"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在
        from sqlalchemy import select
        result = await session.execute(select(Admin).where(Admin.username == "admin"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("管理员账号已存在，跳过创建")
            return
        
        # 创建默认管理员
        admin = Admin(
            username="admin",
            password_hash=get_password_hash("admin123"),
            nickname="系统管理员",
            role="super_admin",
            status=1
        )
        
        session.add(admin)
        await session.commit()
        
        print("✅ 管理员账号创建成功！")
        print("用户名: admin")
        print("密码: admin123")
        print("⚠️  请尽快修改默认密码！")


if __name__ == "__main__":
    asyncio.run(create_admin())
