"""
数据库初始化脚本
"""
import asyncio
import uuid
from sqlalchemy import text

from app.db.database import engine, Base, AsyncSessionLocal
from app.models import User, Device, DeliveryOrder, WalletRecord, WithdrawRecord


async def create_tables():
    """创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建成功")


async def create_test_data():
    """创建测试数据"""
    async with AsyncSessionLocal() as session:
        # 检查是否已有数据
        result = await session.execute(text("SELECT COUNT(*) FROM devices"))
        count = result.scalar()
        
        if count > 0:
            print("ℹ️  测试数据已存在，跳过创建")
            return
        
        # 创建测试设备
        devices = [
            Device(
                device_id="DEV001",
                name="阳光花园A区回收箱",
                address="阳光花园A区1号楼北侧",
                latitude=39.9042,
                longitude=116.4074,
                device_secret="secret_dev001_" + uuid.uuid4().hex[:16],
                unit_price=0.30,
                status="online"
            ),
            Device(
                device_id="DEV002",
                name="幸福小区回收箱",
                address="幸福小区中心广场",
                latitude=39.9142,
                longitude=116.4174,
                device_secret="secret_dev002_" + uuid.uuid4().hex[:16],
                unit_price=0.30,
                status="online"
            ),
            Device(
                device_id="DEV003",
                name="科技园B座回收箱",
                address="科技园B座一楼大厅",
                latitude=39.8942,
                longitude=116.3974,
                device_secret="secret_dev003_" + uuid.uuid4().hex[:16],
                unit_price=0.35,
                status="online"
            )
        ]
        
        for device in devices:
            session.add(device)
        
        await session.commit()
        print("✅ 测试数据创建成功")
        
        # 打印设备密钥(用于测试)
        print("\n📋 测试设备信息:")
        for device in devices:
            print(f"   设备ID: {device.device_id}")
            print(f"   名称: {device.name}")
            print(f"   密钥: {device.device_secret}")
            print()


async def main():
    """主函数"""
    print("🚀 开始初始化数据库...")
    
    try:
        await create_tables()
        await create_test_data()
        print("\n✅ 数据库初始化完成!")
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

