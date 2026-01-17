#!/bin/bash
# 管理后台快速启动脚本

echo "🚀 启动智能旧衣回收箱管理后台..."
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js"
    exit 1
fi

echo "✅ Node.js 版本: $(node -v)"
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
    echo ""
fi

# 检查配置文件
if [ ! -f "vite.config.js" ]; then
    echo "❌ vite.config.js 文件不存在"
    exit 1
fi

echo "📋 配置信息："
echo "   - 前端地址: http://42.194.134.223:3000"
echo "   - 后端代理: http://localhost:8000"
echo "   - 登录账号: admin / admin123"
echo ""

# 启动服务
echo "🎯 启动开发服务器..."
echo "   访问地址: http://42.194.134.223:3000"
echo "   按 Ctrl+C 停止服务"
echo ""

npm run dev
