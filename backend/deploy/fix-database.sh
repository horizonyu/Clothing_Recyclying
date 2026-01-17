#!/bin/bash
# 修复数据库连接问题的脚本

echo "🔍 检查数据库配置..."

cd /home/ubuntu/yzh/code/Clothing_Recyclying/backend/deploy

# 1. 检查 .env 文件中的 DATABASE_URL
echo ""
echo "=== 检查 .env 文件 ==="
if [ -f "../.env" ]; then
    echo "✅ .env 文件存在"
    echo "DATABASE_URL 配置："
    grep "^DATABASE_URL=" ../.env || echo "❌ 未找到 DATABASE_URL 配置"
else
    echo "❌ .env 文件不存在"
fi

# 2. 检查 MySQL 容器状态
echo ""
echo "=== 检查 MySQL 容器 ==="
docker ps | grep mysql || echo "❌ MySQL 容器未运行"

# 3. 测试 MySQL 连接
echo ""
echo "=== 测试 MySQL 连接 ==="
docker exec clothing-recycle-mysql mysql -urecycle -precycle123456 -e "SELECT 1" 2>/dev/null && echo "✅ 使用 recycle/recycle123456 连接成功" || echo "❌ 连接失败"

docker exec clothing-recycle-mysql mysql -uroot -proot123456 -e "SELECT 1" 2>/dev/null && echo "✅ 使用 root/root123456 连接成功" || echo "❌ 连接失败"

# 4. 显示修复建议
echo ""
echo "📋 修复建议："
echo ""
echo "如果 DATABASE_URL 使用 root 用户，但密码不对："
echo "  方案1: 修改 .env 文件中的密码为 root123456"
echo "  方案2: 或修改 DATABASE_URL 使用 recycle 用户"
echo ""
echo "正确的 DATABASE_URL 格式应该是："
echo "  mysql+aiomysql://recycle:recycle123456@mysql:3306/clothing_recycle"
echo "  或"
echo "  mysql+aiomysql://root:root123456@mysql:3306/clothing_recycle"
echo ""
