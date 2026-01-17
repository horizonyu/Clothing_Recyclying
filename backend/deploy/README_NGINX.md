# Nginx 配置说明

## 配置文件说明

| 配置文件 | 用途 | SSL 证书要求 |
|---------|------|------------|
| `nginx.conf` | 生产环境（HTTPS） | ✅ 需要 |
| `nginx.conf.http-only` | 开发/测试（HTTP） | ❌ 不需要 |

## 使用方式

### 方式一：HTTP 版本（推荐用于开发/测试）

通过 IP 地址访问，无需 SSL 证书：

```bash
cd backend/deploy

# 使用 HTTP 版本配置
docker-compose -f docker-compose-http.yml up -d

# 查看日志
docker-compose -f docker-compose-http.yml logs -f nginx
```

访问地址：
- API: `http://服务器IP/api/v1/...`
- 文档: `http://服务器IP/docs`
- 健康检查: `http://服务器IP/health`

### 方式二：HTTPS 版本（生产环境）

需要先配置 SSL 证书：

```bash
# 1. 创建 SSL 证书目录
mkdir -p backend/deploy/nginx/ssl

# 2. 将证书文件复制到该目录
# - fullchain.pem
# - privkey.pem

# 3. 使用完整版配置启动
docker-compose up -d
```

## 快速切换

如果当前正在使用 `docker-compose-simple.yml`，想添加 Nginx HTTP 代理：

```bash
cd backend/deploy

# 停止当前服务
docker-compose -f docker-compose-simple.yml down

# 使用 HTTP 版本配置启动（包含 Nginx）
docker-compose -f docker-compose-http.yml up -d

# 查看状态
docker ps
```

## 验证

```bash
# 测试 Nginx 是否正常
curl http://localhost/health

# 应该返回：{"status":"healthy"}

# 查看 Nginx 日志
docker logs clothing-recycle-nginx
```

## 端口说明

- **80**: Nginx HTTP 代理（通过 Nginx 访问 API）
- **8000**: API 直接访问（不经过 Nginx）
- **443**: HTTPS（需要 SSL 证书）

## 推荐配置

| 环境 | 推荐配置 | 访问方式 |
|-----|---------|---------|
| 开发/测试 | `docker-compose-http.yml` | `http://IP` |
| 生产（无证书） | `docker-compose-simple.yml` | `http://IP:8000` |
| 生产（有证书） | `docker-compose.yml` | `https://域名` |
