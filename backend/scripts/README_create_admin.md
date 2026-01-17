# 创建管理员账号

## 方法一：在 Docker 容器内运行（推荐）

如果使用 Docker 部署，请在容器内运行脚本：

```bash
# 进入容器
docker exec -it clothing-recycle-api bash

# 在容器内运行脚本
python scripts/create_admin.py

# 或直接执行（不进入容器）
docker exec -it clothing-recycle-api python scripts/create_admin.py
```

## 方法二：本地环境运行

如果需要在本地运行（非Docker环境），需要先安装依赖：

```bash
cd backend

# 创建虚拟环境（如果还没有）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行脚本
python scripts/create_admin.py
```

## 方法三：使用 Docker Compose（如果使用 docker-compose）

```bash
cd backend/deploy

# 使用 docker-compose 执行
docker-compose -f docker-compose-simple.yml exec api python scripts/create_admin.py
```

## 默认账号

创建成功后会显示：
- 用户名: `admin`
- 密码: `admin123`

⚠️ **重要：首次登录后请立即修改默认密码！**
