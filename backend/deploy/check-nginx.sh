#!/bin/bash
# Nginx 502 错误排查脚本

echo "🔍 开始排查 Nginx 502 错误..."
echo ""

# 1. 检查容器状态
echo "=== 1. 容器状态 ==="
docker ps | grep clothing-recycle
echo ""

# 2. 检查 API 容器是否正常运行
echo "=== 2. API 容器日志（最后20行） ==="
docker logs clothing-recycle-api --tail 20 2>/dev/null || echo "❌ API 容器不存在或无法访问"
echo ""

# 3. 检查 API 服务是否在容器内正常运行
echo "=== 3. 测试 API 容器内的服务 ==="
docker exec clothing-recycle-api curl -s http://localhost:8000/health 2>/dev/null || echo "❌ API 服务在容器内无法访问"
echo ""

# 4. 检查 Nginx 配置
echo "=== 4. Nginx 配置检查 ==="
docker exec clothing-recycle-nginx nginx -t 2>/dev/null || echo "❌ Nginx 配置有误"
echo ""

# 5. 检查网络连接
echo "=== 5. 网络连接测试 ==="
echo "从 Nginx 容器测试 API 连接："
docker exec clothing-recycle-nginx wget -qO- http://api:8000/health 2>/dev/null || echo "❌ Nginx 无法连接到 API 服务（网络问题）"
echo ""

# 6. 检查 Docker 网络
echo "=== 6. Docker 网络检查 ==="
docker network inspect clothing-network 2>/dev/null | grep -A 5 "Containers" || echo "❌ 网络不存在或容器未加入网络"
echo ""

echo "📋 常见解决方案："
echo ""
echo "1. 如果 API 容器日志显示错误："
echo "   - 查看完整日志: docker logs clothing-recycle-api"
echo "   - 检查数据库连接配置"
echo ""
echo "2. 如果网络连接失败："
echo "   - 确认所有容器都在同一个网络: clothing-network"
echo "   - 重新创建网络: docker network create clothing-network"
echo ""
echo "3. 如果 API 服务未启动："
echo "   - 重启 API 容器: docker restart clothing-recycle-api"
echo "   - 或重新构建: docker-compose -f docker-compose-http.yml up -d --build api"
echo ""
