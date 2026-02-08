# Docker 代码更新指南

## 📋 问题说明

当你在服务器上通过 `git pull` 更新了代码后，发现 Docker 容器内的代码仍然是旧版本，导致应用报错或功能异常。

## 🔍 问题原因

Docker 容器中的代码是在**构建镜像时**复制进去的（通过 Dockerfile 中的 `COPY . .` 命令），而不是通过 volume 挂载。这意味着：

- ✅ 服务器上的代码已更新（通过 `git pull`）
- ❌ 容器内的代码还是旧的（构建时的版本）
- ❌ 重启容器不会更新代码（需要重新构建镜像）

## 💡 解决方案：重新构建 Docker 镜像

### 前置条件

1. 确保服务器上的代码已更新：
   ```bash
   cd /home/ubuntu/yzh/code/Clothing_Recyclying
   git pull origin main
   ```

2. 确认代码更新成功：
   ```bash
   # 检查关键文件是否已更新
   git log --oneline -5
   git status
   ```

### 操作步骤

#### 步骤 1：进入部署目录

```bash
cd /home/ubuntu/yzh/code/Clothing_Recyclying/backend/deploy
```

#### 步骤 2：停止并删除旧容器

```bash
# 停止所有服务
docker-compose -f docker-compose-http.yml down

# 确认容器已停止
docker ps | grep clothing-recycle
```

> ⚠️ **注意**：`down` 命令会停止并删除容器，但**不会删除数据卷**（如 MySQL 数据、Redis 数据），所以数据是安全的。

#### 步骤 3：重新构建镜像

```bash
# 重新构建 API 镜像（包含最新代码）
docker-compose -f docker-compose-http.yml build --no-cache api
```

**参数说明**：
- `--no-cache`：不使用缓存，确保完全重新构建
- `api`：只构建 API 服务（其他服务如 MySQL、Redis 使用现成镜像，无需重建）

**构建时间**：通常需要 2-5 分钟，取决于网络速度和依赖包数量。

#### 步骤 4：启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose-http.yml up -d

# 查看服务状态
docker-compose -f docker-compose-http.yml ps
```

#### 步骤 5：查看日志确认启动成功

```bash
# 查看 API 容器日志（最后50行）
docker logs clothing-recycle-api --tail 50

# 实时查看日志（按 Ctrl+C 退出）
docker logs clothing-recycle-api -f
```

**成功标志**：
- 看到 `Application startup complete` 或类似信息
- 没有 `SyntaxError`、`ImportError` 等错误
- 服务状态显示为 `Up`

### 验证修复

#### 方法 1：检查代码语法

```bash
# 检查关键文件语法是否正确
docker exec clothing-recycle-api python -m py_compile /app/app/api/v1/admin_device.py && echo "✅ 语法正确"
docker exec clothing-recycle-api python -m py_compile /app/app/api/v1/admin_order.py && echo "✅ 语法正确"
docker exec clothing-recycle-api python -m py_compile /app/app/api/v1/admin_user.py && echo "✅ 语法正确"
```

#### 方法 2：检查容器内的代码版本

```bash
# 查看容器内文件内容（确认是最新版本）
docker exec clothing-recycle-api cat /app/app/api/v1/admin_device.py | head -35

# 或检查文件的最后修改时间
docker exec clothing-recycle-api ls -la /app/app/api/v1/admin_device.py
```

#### 方法 3：测试 API 接口

```bash
# 测试健康检查接口
curl http://localhost:8000/health

# 应该返回：{"status":"healthy"}
```

#### 方法 4：检查日志中是否有错误

```bash
# 查看最近的错误日志
docker logs clothing-recycle-api --tail 100 | grep -i "error\|exception\|traceback" || echo "✅ 没有错误"
```

## 📝 完整命令清单（一键执行）

如果你已经确认代码已更新，可以一次性执行以下命令：

```bash
cd /home/ubuntu/yzh/code/Clothing_Recyclying/backend/deploy && \
docker-compose -f docker-compose-http.yml down && \
docker-compose -f docker-compose-http.yml build --no-cache api && \
docker-compose -f docker-compose-http.yml up -d && \
sleep 5 && \
docker logs clothing-recycle-api --tail 30
```

## 🔄 其他 Docker Compose 配置文件

如果你使用的是其他配置文件，替换命令中的文件名即可：

| 配置文件 | 命令 |
|---------|------|
| `docker-compose-http.yml` | `docker-compose -f docker-compose-http.yml ...` |
| `docker-compose-simple.yml` | `docker-compose -f docker-compose-simple.yml ...` |
| `docker-compose.yml` | `docker-compose ...` |

## ⚠️ 注意事项

1. **数据安全**：
   - `docker-compose down` 不会删除数据卷（MySQL、Redis 数据）
   - 如果需要完全清理，使用 `docker-compose down -v`（⚠️ 会删除所有数据）

2. **服务中断**：
   - 重建过程中服务会短暂中断（通常 2-5 分钟）
   - 建议在业务低峰期执行

3. **网络问题**：
   - 如果构建时下载依赖包失败，检查网络连接
   - 可以使用国内镜像源加速

4. **磁盘空间**：
   - 重新构建会创建新镜像，旧镜像会变成 `<none>`（悬空镜像）
   - 定期清理：`docker image prune -f`

## 🐛 常见问题

### Q1: 构建失败，提示 "ModuleNotFoundError"

**原因**：`requirements.txt` 中可能添加了新依赖

**解决**：
```bash
# 确保 requirements.txt 已更新
cd /home/ubuntu/yzh/code/Clothing_Recyclying/backend
git pull
cat requirements.txt

# 重新构建
cd deploy
docker-compose -f docker-compose-http.yml build --no-cache api
```

### Q2: 构建很慢，如何加速？

**方法 1**：使用国内镜像源（修改 Dockerfile 或使用代理）

**方法 2**：只构建必要的层
```bash
# 如果只是代码更新，可以尝试不使用 --no-cache（但可能不会完全更新）
docker-compose -f docker-compose-http.yml build api
```

### Q3: 容器启动后立即退出

**排查步骤**：
```bash
# 1. 查看详细日志
docker logs clothing-recycle-api

# 2. 检查环境变量
docker exec clothing-recycle-api env | grep -E "(DATABASE|REDIS)"

# 3. 检查配置文件
docker exec clothing-recycle-api cat /app/.env
```

### Q4: 如何确认代码已更新？

```bash
# 方法1：检查文件内容
docker exec clothing-recycle-api grep -n "try:" /app/app/api/v1/admin_device.py

# 方法2：检查 Git 提交信息（如果代码中包含）
docker exec clothing-recycle-api cat /app/app/__init__.py 2>/dev/null || echo "无版本信息"

# 方法3：对比文件修改时间
docker exec clothing-recycle-api stat /app/app/api/v1/admin_device.py
```

## 📚 相关文档

- [Docker 部署指南](../backend/deploy/README.md)
- [故障排查指南](../backend/deploy/TROUBLESHOOTING.md)
- [从零部署完整指南](./从零部署完整指南.md)

## 🎯 快速参考

```bash
# 更新代码
cd /home/ubuntu/yzh/code/Clothing_Recyclying && git pull

# 重新构建并启动
cd backend/deploy
docker-compose -f docker-compose-http.yml down
docker-compose -f docker-compose-http.yml build --no-cache api
docker-compose -f docker-compose-http.yml up -d

# 验证
docker logs clothing-recycle-api --tail 50
curl http://localhost:8000/health
```

---

**最后更新**：2026-02-07  
**适用版本**：v1.0+
