#!/bin/bash
# 修复管理后台统计接口错误的脚本

echo "🔍 开始诊断管理后台统计接口问题..."
echo ""

# 1. 检查 API 容器状态
echo "=== 1. API 容器状态 ==="
docker ps | grep clothing-recycle-api || echo "❌ API 容器未运行"
echo ""

# 2. 查看最近的错误日志
echo "=== 2. API 容器最近错误日志（最后50行） ==="
docker logs clothing-recycle-api --tail 50 2>&1 | grep -i -E "(error|exception|traceback|failed)" || echo "未找到明显的错误信息"
echo ""

# 3. 测试接口
echo "=== 3. 测试统计接口 ==="
echo "提示：需要先登录获取 token"
echo "执行以下命令测试："
echo ""
echo "# 1. 登录获取 token"
echo "TOKEN=\$(curl -s -X POST http://localhost:8000/api/v1/admin/auth/login \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"username\":\"admin\",\"password\":\"admin123\"}' | grep -o '\"token\":\"[^\"]*' | cut -d'\"' -f4)"
echo ""
echo "# 2. 测试统计接口"
echo "curl -v -X GET \"http://localhost:8000/api/v1/admin/dashboard/stats?period=7days\" \\"
echo "  -H \"Authorization: Bearer \$TOKEN\""
echo ""

# 4. 检查代码是否已更新
echo "=== 4. 检查代码文件 ==="
if docker exec clothing-recycle-api test -f /app/app/api/v1/admin.py; then
    echo "✅ 代码文件存在"
    # 检查是否有 try-except
    if docker exec clothing-recycle-api grep -q "except Exception as e" /app/app/api/v1/admin.py; then
        echo "✅ 错误处理代码已存在"
    else
        echo "⚠️  错误处理代码可能未更新，需要重新构建容器"
    fi
else
    echo "❌ 代码文件不存在"
fi
echo ""

# 5. 重启建议
echo "=== 5. 重启命令 ==="
echo ""
echo "方案A：简单重启（推荐，如果代码已通过卷挂载）"
echo "  cd /home/ubuntu/yzh/code/Clothing_Recyclying/backend/deploy"
echo "  docker-compose -f docker-compose-http.yml restart api"
echo ""
echo "方案B：重新构建并启动（如果代码需要重新构建到镜像中）"
echo "  cd /home/ubuntu/yzh/code/Clothing_Recyclying/backend/deploy"
echo "  docker-compose -f docker-compose-http.yml up -d --build api"
echo ""
echo "方案C：查看实时日志（重启后执行）"
echo "  docker logs clothing-recycle-api -f"
echo ""

echo "📋 如果问题仍然存在，请执行以下命令查看详细错误："
echo "  docker logs clothing-recycle-api --tail 100 | grep -A 20 -i error"
