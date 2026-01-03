# 智能旧衣回收箱 - 微信小程序

## 项目简介

这是智能旧衣回收箱系统的微信小程序端，用户可以通过小程序扫码领取回收金额、查看投递记录、管理钱包等。

## 快速开始

### 1. 环境准备

1. **下载微信开发者工具**
   - 访问 https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html
   - 下载并安装对应系统版本

2. **注册小程序账号**（可选，用于真机预览和发布）
   - 访问 https://mp.weixin.qq.com/
   - 注册小程序账号，获取 AppID

### 2. 导入项目

1. 打开微信开发者工具
2. 点击「+」按钮创建项目
3. 选择项目目录为 `miniprogram/` 文件夹
4. AppID 可以：
   - 使用测试号（点击「测试号」）
   - 填写你的正式 AppID
5. 点击「确定」导入项目

### 3. 配置后端地址

修改 `config/index.js` 文件：

```javascript
// 开发环境
development: {
  API_BASE_URL: 'http://localhost:8000/api/v1',  // 改为你的后端地址
  // ...
},

// 生产环境  
production: {
  API_BASE_URL: 'https://api.yourdomain.com/api/v1',  // 改为你的正式后端地址
  // ...
}
```

### 4. 开发调试

1. **开启不校验域名**（开发阶段）
   - 点击右上角「详情」
   - 勾选「不校验合法域名...」

2. **编译预览**
   - 点击「编译」按钮
   - 在模拟器中查看效果

3. **真机调试**
   - 点击「预览」按钮
   - 用微信扫描二维码

## 目录结构

```
miniprogram/
├── app.js                 # 入口文件
├── app.json               # 全局配置
├── app.wxss               # 全局样式
├── project.config.json    # 项目配置
│
├── config/                # 配置文件
│   └── index.js          # 环境配置
│
├── utils/                 # 工具函数
│   ├── request.js        # 网络请求封装
│   └── util.js           # 通用工具
│
├── services/              # API服务
│   ├── user.js           # 用户服务
│   ├── order.js          # 订单服务
│   └── device.js         # 设备服务
│
├── pages/                 # 页面
│   ├── index/            # 首页
│   ├── scan/             # 扫码页面 ⭐核心
│   ├── claim-success/    # 领取成功
│   ├── orders/           # 订单列表
│   ├── order-detail/     # 订单详情
│   ├── wallet/           # 钱包
│   ├── withdraw/         # 提现
│   ├── profile/          # 个人中心
│   └── nearby/           # 附近回收箱
│
└── images/                # 图片资源
```

## 核心功能

### 扫码领取流程

1. 用户在回收箱投递衣物
2. 回收箱屏幕显示二维码
3. 用户打开小程序扫码
4. 确认信息后领取金额
5. 金额入账到钱包

### 页面说明

| 页面 | 路径 | 功能 |
|-----|------|------|
| 首页 | /pages/index/index | 展示用户数据、快捷入口 |
| 扫码 | /pages/scan/scan | 扫描回收箱二维码 |
| 记录 | /pages/orders/orders | 查看投递历史 |
| 我的 | /pages/profile/profile | 个人中心 |
| 钱包 | /pages/wallet/wallet | 余额和交易记录 |
| 提现 | /pages/withdraw/withdraw | 申请提现 |

## 图片资源

需要准备以下图片资源放入 `images/` 目录：

```
images/
├── tab/                   # TabBar图标
│   ├── home.png          # 首页图标
│   ├── home-active.png   # 首页选中图标
│   ├── scan.png          # 扫码图标
│   ├── scan-active.png   # 扫码选中图标
│   ├── order.png         # 订单图标
│   ├── order-active.png  # 订单选中图标
│   ├── user.png          # 我的图标
│   └── user-active.png   # 我的选中图标
│
├── default-avatar.png     # 默认头像
├── scan-frame.png         # 扫码框图片
├── marker.png             # 地图标记图标
└── share-cover.png        # 分享封面图
```

**图标建议**：
- TabBar图标尺寸：81×81px（PNG格式，透明背景）
- 可使用 [iconfont](https://www.iconfont.cn/) 下载

## 常见问题

### 1. 网络请求失败

**解决方案**：
- 开发阶段：勾选「不校验合法域名」
- 正式环境：在微信公众平台配置服务器域名

### 2. 扫码功能不可用

**原因**：模拟器不支持扫码
**解决方案**：使用真机预览测试

### 3. 位置权限被拒绝

**解决方案**：
- 引导用户到设置页开启权限
- 在 `app.json` 中配置权限描述

### 4. 页面白屏

**排查步骤**：
1. 查看 Console 面板是否有报错
2. 检查页面路径是否正确
3. 检查数据绑定是否正确

## 发布上线

1. **上传代码**
   - 点击「上传」按钮
   - 填写版本号和备注

2. **提交审核**
   - 登录微信公众平台
   - 进入「版本管理」
   - 提交审核

3. **发布**
   - 审核通过后点击「发布」

## 联系我们

如有问题，请联系技术支持。

