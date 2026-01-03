# 云服务器部署指南

本文档介绍如何将后端服务部署到 Linux 云服务器（Ubuntu/CentOS）。

## 部署方式选择

| 方式 | 优点 | 适用场景 |
|-----|------|---------|
| **Docker 部署** ⭐推荐 | 环境隔离、部署简单、易于扩展 | 生产环境 |
| 传统部署 | 资源占用少 | 小型服务器 |

---

## 方式一：Docker 部署（推荐）

### 1. 安装 Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录使 docker 组生效
exit
```

### 2. 上传代码到服务器

```bash
# 本地执行，将代码上传到服务器
scp -r /Users/nicolas/work/code/Clothing_Recycle root@your-server-ip:/opt/

# 或使用 git clone
ssh root@your-server-ip
cd /opt
git clone your-repo-url Clothing_Recycle
```

### 3. 配置环境变量

```bash
cd /opt/Clothing_Recycle/backend
cp env.example.txt .env
vi .env
```

修改 `.env` 文件：

```ini
APP_ENV=production
DEBUG=false
SECRET_KEY=生成一个随机字符串

# Docker 中 MySQL 地址
DATABASE_URL=mysql+aiomysql://recycle:your_password@mysql:3306/clothing_recycle

# Docker 中 Redis 地址
REDIS_URL=redis://redis:6379/0

# 微信配置
WECHAT_APPID=你的AppID
WECHAT_SECRET=你的AppSecret

# JWT密钥
JWT_SECRET_KEY=生成一个随机字符串
```

### 4. 启动服务

```bash
cd /opt/Clothing_Recycle/backend/deploy

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 初始化数据库
docker-compose exec api python -m app.db.init_db
```

### 5. 验证部署

```bash
curl http://localhost:8000/health
# 返回 {"status":"healthy"} 表示成功
```

---

## 方式二：传统部署

### 1. 安装系统依赖

```bash
# Ubuntu
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip mysql-server redis-server nginx

# CentOS
sudo yum install -y python3 python3-pip mysql-server redis nginx
```

### 2. 配置 MySQL

```bash
# 启动 MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置
sudo mysql_secure_installation

# 创建数据库和用户
sudo mysql -u root -p
```

```sql
CREATE DATABASE clothing_recycle CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'recycle'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON clothing_recycle.* TO 'recycle'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. 配置 Redis

```bash
sudo systemctl start redis
sudo systemctl enable redis
```

### 4. 部署应用

```bash
# 创建应用目录
sudo mkdir -p /opt/Clothing_Recycle
cd /opt/Clothing_Recycle

# 上传代码（或 git clone）
# ...

cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example.txt .env
vi .env
```

### 5. 配置 Systemd 服务

```bash
sudo cp deploy/clothing-recycle.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start clothing-recycle
sudo systemctl enable clothing-recycle

# 查看状态
sudo systemctl status clothing-recycle
```

### 6. 配置 Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/clothing-recycle
sudo ln -s /etc/nginx/sites-available/clothing-recycle /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 配置 HTTPS（必须）

微信小程序要求后端必须使用 HTTPS。

### 方式1：使用 Let's Encrypt（免费）

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书（替换为你的域名）
sudo certbot --nginx -d api.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### 方式2：使用云服务商 SSL

1. 在云服务商（阿里云/腾讯云）申请免费 SSL 证书
2. 下载证书文件
3. 配置 Nginx（参考 nginx-ssl.conf）

---

## 配置微信小程序域名

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 进入「开发管理」→「开发设置」→「服务器域名」
3. 添加以下域名：
   - request合法域名：`https://api.yourdomain.com`
   - uploadFile合法域名：`https://api.yourdomain.com`

---

## 常用命令

```bash
# Docker 方式
docker-compose up -d          # 启动服务
docker-compose down           # 停止服务
docker-compose logs -f api    # 查看日志
docker-compose restart api    # 重启 API 服务

# 传统方式
sudo systemctl start clothing-recycle    # 启动
sudo systemctl stop clothing-recycle     # 停止
sudo systemctl restart clothing-recycle  # 重启
sudo journalctl -u clothing-recycle -f   # 查看日志
```

---

## 防火墙配置

```bash
# Ubuntu (ufw)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 安全建议

1. **修改默认密码**：MySQL、Redis 等服务
2. **限制端口访问**：只开放 80/443 端口
3. **定期更新**：系统和依赖包
4. **备份数据**：定期备份数据库
5. **监控告警**：配置服务监控

