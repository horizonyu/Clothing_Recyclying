# 容器重启问题排查指南

## 问题1：Nginx 容器一直重启

### 原因
Nginx 配置文件中配置了 SSL 证书，但证书文件不存在。

### 解决方案

**方案A：使用简化版配置（不包含 Nginx）**

```bash
# 停止当前服务
docker-compose down

# 使用简化版配置启动（不包含 Nginx）
docker-compose -f docker-compose-simple.yml up -d
```

**方案B：修复 Nginx 配置（需要 SSL 证书）**

1. 创建 SSL 证书目录：
```bash
mkdir -p nginx/ssl
```

2. 如果有证书，将证书文件复制到 `nginx/ssl/` 目录：
   - `fullchain.pem`
   - `privkey.pem`

3. 如果没有证书，可以临时禁用 HTTPS（不推荐生产环境）：
   - 注释掉 nginx.conf 中的 HTTPS server 块，只保留 HTTP

**方案C：临时禁用 Nginx（推荐）**

如果暂时不需要 Nginx，可以停止并移除它：

```bash
# 停止并移除 Nginx 容器
docker stop clothing-recycle-nginx
docker rm clothing-recycle-nginx

# 或者使用 docker-compose，但不包含 nginx 服务
docker-compose up -d api mysql redis
```

## 问题2：API 容器一直重启

### 排查步骤

1. **查看 API 容器日志**
```bash
# 查看最近的日志
docker logs clothing-recycle-api --tail 100

# 实时查看日志
docker logs clothing-recycle-api -f
```

2. **常见原因和解决方案**

#### A. 数据库连接失败

**错误信息**：`Can't connect to MySQL server`

**解决方案**：
- 检查 `.env` 文件中的 `DATABASE_URL` 是否正确
- 确保 MySQL 容器正常运行：`docker ps | grep mysql`
- 检查网络连接：`docker network inspect clothing-network`

```bash
# 检查数据库连接
docker exec -it clothing-recycle-mysql mysql -urecycle -precycle123456 -e "SELECT 1"
```

#### B. 配置文件错误

**错误信息**：`Config file error` 或 `Environment variable error`

**解决方案**：
```bash
# 检查 .env 文件是否存在
ls -la backend/.env

# 检查 .env 文件格式
cat backend/.env
```

确保 `.env` 文件中包含必要的配置项：
- `DATABASE_URL`
- `REDIS_URL`
- `WECHAT_APPID`
- `WECHAT_SECRET`
- `JWT_SECRET_KEY`
- `SECRET_KEY`

#### C. 缺少依赖或代码错误

**错误信息**：`ModuleNotFoundError` 或 `ImportError`

**解决方案**：
```bash
# 重新构建镜像
cd backend/deploy
docker-compose build --no-cache api

# 重新启动
docker-compose up -d api
```

#### D. 端口冲突

**错误信息**：`Address already in use`

**解决方案**：
```bash
# 检查端口占用
netstat -tlnp | grep 8000

# 或者修改 docker-compose.yml 中的端口映射
ports:
  - "8001:8000"  # 改为其他端口
```

## 快速诊断命令

```bash
# 1. 查看所有容器状态
docker ps -a

# 2. 查看 API 容器日志
docker logs clothing-recycle-api --tail 50

# 3. 查看 Nginx 容器日志
docker logs clothing-recycle-nginx --tail 50

# 4. 进入 API 容器检查
docker exec -it clothing-recycle-api bash

# 5. 测试数据库连接
docker exec -it clothing-recycle-api python -c "from app.db.database import engine; print('DB OK')"

# 6. 检查环境变量
docker exec -it clothing-recycle-api env | grep -E "(DATABASE|REDIS|WECHAT)"
```

## 推荐的启动方式

### 开发/测试环境（推荐）

使用简化版配置，不包含 Nginx：

```bash
cd backend/deploy
docker-compose -f docker-compose-simple.yml up -d
```

### 生产环境

1. 先准备好 SSL 证书
2. 使用完整版配置：

```bash
cd backend/deploy
docker-compose up -d
```

## 完整重置步骤

如果问题持续，可以完全重置：

```bash
# 1. 停止所有容器
docker-compose down

# 2. 清理未使用的资源（可选）
docker system prune -f

# 3. 重新构建镜像
docker-compose build --no-cache

# 4. 启动服务
docker-compose -f docker-compose-simple.yml up -d

# 5. 查看日志
docker-compose -f docker-compose-simple.yml logs -f
```
