#!/bin/bash

# 智能旧衣回收箱 - 快速部署脚本
# 使用方法: bash deploy.sh

set -e

echo "=========================================="
echo "  智能旧衣回收箱 - 后端部署脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装${NC}"
        echo "请先安装 Docker: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker 已安装${NC}"
}

# 检查 Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}⚠ Docker Compose 未安装，正在安装...${NC}"
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    echo -e "${GREEN}✓ Docker Compose 已安装${NC}"
}

# 检查 .env 文件
check_env() {
    if [ ! -f "../.env" ]; then
        echo -e "${YELLOW}⚠ .env 文件不存在，正在创建...${NC}"
        cp ../env.example.txt ../.env
        echo -e "${YELLOW}请编辑 .env 文件配置微信 AppID 等信息${NC}"
        echo "vi ../.env"
        exit 1
    fi
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
}

# 部署服务
deploy() {
    echo ""
    echo "正在启动服务..."
    
    # 使用简化版配置（不含 Nginx）
    docker-compose -f docker-compose-simple.yml up -d --build
    
    echo ""
    echo "等待服务启动..."
    sleep 10
    
    # 初始化数据库
    echo "正在初始化数据库..."
    docker-compose -f docker-compose-simple.yml exec -T api python -m app.db.init_db
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  ✅ 部署完成！"
    echo "==========================================${NC}"
    echo ""
    echo "API 地址: http://$(hostname -I | awk '{print $1}'):8000"
    echo "API 文档: http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo ""
    echo "常用命令:"
    echo "  查看日志: docker-compose -f docker-compose-simple.yml logs -f"
    echo "  停止服务: docker-compose -f docker-compose-simple.yml down"
    echo "  重启服务: docker-compose -f docker-compose-simple.yml restart"
    echo ""
}

# 主流程
main() {
    cd "$(dirname "$0")"
    
    check_docker
    check_docker_compose
    check_env
    deploy
}

main

