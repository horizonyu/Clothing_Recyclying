# 智能旧衣回收箱 - 管理后台

基于 Vue3 + Element Plus 构建的管理后台系统。

## 快速开始

### 1. 安装依赖

```bash
cd admin
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

## 功能模块

- ✅ 工作台/仪表盘
- ✅ 设备管理
- ✅ 订单管理
- ✅ 用户管理
- ✅ 财务管理
- ⏳ 统计报表（开发中）
- ⏳ 系统管理（开发中）

## 技术栈

- Vue 3
- Element Plus
- Vue Router
- Pinia
- Axios
- ECharts
- Vite

## 默认账号

首次使用需要创建管理员账号（通过后端API或数据库直接插入）。

默认测试账号：
- 用户名: admin
- 密码: admin123

## 项目结构

```
admin/
├── src/
│   ├── api/          # API接口
│   ├── assets/       # 静态资源
│   ├── components/   # 公共组件
│   ├── layouts/      # 布局组件
│   ├── router/       # 路由配置
│   ├── stores/       # 状态管理
│   ├── styles/       # 样式文件
│   ├── utils/        # 工具函数
│   └── views/        # 页面视图
├── package.json
└── vite.config.js
```
