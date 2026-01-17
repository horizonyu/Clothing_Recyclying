#!/bin/bash
# 快速修复容器重启问题的脚本

echo "🔍 开始诊断容器问题..."

# 检查容器状态
echo ""
echo "=== 当前容器状态 ==="
docker ps -a | grep clothing-recycle

# 停止所有容器
echo ""
echo "🛑 停止所有容器..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose-simple.yml down 2>/dev/null || true

# 查看 API 容器最后100行日志
echo ""
echo "=== API 容器最后日志 ==="
docker logs clothing-recycle-api --tail 100 2>/dev/null || echo "API 容器不存在"

# 查看 Nginx 容器最后100行日志
echo ""
echo "=== Nginx 容器最后日志 ==="
docker logs clothing-recycle-nginx --tail 100 2>/dev/null || echo "Nginx 容器不存在"

echo ""
echo "📋 建议的解决方案："
echo ""
echo "1. 如果 Nginx 报错（证书文件不存在）："
echo "   使用简化版配置启动：docker-compose -f docker-compose-simple.yml up -d"
echo ""
echo "2. 如果 API 报错（数据库连接失败）："
echo "   检查 .env 文件中的 DATABASE_URL 配置"
echo ""
echo "3. 如果需要查看详细错误："
echo "   docker logs clothing-recycle-api -f"
echo ""
echo "4. 完全重置（会清理数据，谨慎使用）："
echo "   docker-compose down -v"
echo "   docker-compose -f docker-compose-simple.yml up -d --build"
echo ""
