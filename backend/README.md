# 智能旧衣回收箱 - 后端服务

基于 Python FastAPI 构建的后端 API 服务。

## 快速开始

### 1. 环境要求

- Python 3.9+
- MySQL 8.0+
- Redis 6.0+

### 2. 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置环境变量

复制配置文件并修改：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写数据库等配置。

### 4. 初始化数据库

```bash
# 创建数据库表
python -m app.db.init_db
```

### 5. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend/
├── app/
│   ├── main.py              # 应用入口
│   ├── config.py            # 配置管理
│   ├── api/                  # API路由
│   │   ├── v1/
│   │   │   ├── user.py      # 用户接口
│   │   │   ├── order.py     # 订单接口
│   │   │   ├── device.py    # 设备接口
│   │   │   └── wallet.py    # 钱包接口
│   │   └── deps.py          # 依赖注入
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic模型
│   ├── services/            # 业务逻辑
│   ├── db/                  # 数据库
│   └── utils/               # 工具函数
├── requirements.txt
└── .env.example
```

## API 接口

| 接口 | 方法 | 说明 |
|-----|------|------|
| /api/v1/user/login/wechat | POST | 微信登录 |
| /api/v1/user/profile | GET | 获取用户信息 |
| /api/v1/order/scan | POST | 扫码解析 |
| /api/v1/order/{id}/claim | POST | 领取订单 |
| /api/v1/order/list | GET | 订单列表 |
| /api/v1/wallet/balance | GET | 钱包余额 |
| /api/v1/device/nearby | GET | 附近设备 |

