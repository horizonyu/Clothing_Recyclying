#!/bin/bash
# 诊断管理后台"服务器错误"问题

echo "🔍 诊断管理后台问题..."
echo ""

# 1. 检查 API 容器是否运行
echo "=== 1. 检查 API 容器 ==="
if docker ps | grep -q clothing-recycle-api; then
    echo "✅ API 容器正在运行"
else
    echo "❌ API 容器未运行"
    exit 1
fi

# 2. 测试健康检查
echo ""
echo "=== 2. 测试健康检查 ==="
health=$(curl -s http://localhost:8000/health)
if [ "$health" == '{"status":"healthy"}' ]; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常: $health"
fi

# 3. 测试登录接口
echo ""
echo "=== 3. 测试登录接口 ==="
login_response=$(curl -s -X POST http://localhost:8000/api/v1/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

echo "响应: $login_response"

# 提取 token
token=$(echo $login_response | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -n "$token" ]; then
    echo "✅ 登录成功，Token 已获取"
    
    # 4. 测试获取用户信息
    echo ""
    echo "=== 4. 测试获取用户信息 ==="
    profile_response=$(curl -s -X GET http://localhost:8000/api/v1/admin/auth/profile \
      -H "Authorization: Bearer $token")
    echo "响应: $profile_response"
    
    # 5. 测试获取统计数据
    echo ""
    echo "=== 5. 测试获取统计数据 ==="
    stats_response=$(curl -s -X GET "http://localhost:8000/api/v1/admin/dashboard/stats?period=today" \
      -H "Authorization: Bearer $token")
    echo "响应: $stats_response"
    
    if echo "$stats_response" | grep -q '"code":0'; then
        echo "✅ 统计数据接口正常"
    else
        echo "❌ 统计数据接口异常"
        echo "详细错误: $stats_response"
    fi
else
    echo "❌ 登录失败"
    echo "请检查："
    echo "  1. 管理员账号是否已创建"
    echo "  2. 用户名和密码是否正确"
fi

# 6. 检查数据库表
echo ""
echo "=== 6. 检查数据库表 ==="
tables=$(docker exec -it clothing-recycle-mysql mysql -urecycle -precycle123456 -e "USE clothing_recycle; SHOW TABLES;" 2>/dev/null | grep -E "(admins|delivery_orders|devices)")

if echo "$tables" | grep -q "admins"; then
    echo "✅ admins 表存在"
else
    echo "❌ admins 表不存在，需要初始化数据库"
fi

if echo "$tables" | grep -q "delivery_orders"; then
    echo "✅ delivery_orders 表存在"
else
    echo "⚠️  delivery_orders 表不存在（可能没有数据）"
fi

echo ""
echo "📋 诊断完成"
echo ""
echo "如果登录失败，请运行："
echo "  docker exec -it clothing-recycle-api python scripts/create_admin.py"
echo ""
echo "如果数据库表不存在，请运行："
echo "  docker exec -it clothing-recycle-api python -m app.db.init_db"
