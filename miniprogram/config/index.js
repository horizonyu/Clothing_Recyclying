/**
 * 环境配置文件
 * 根据不同环境切换API地址
 */

// 环境标识: development | production
const ENV = 'development';

// 不同环境的配置
const config = {
  // 开发环境
  development: {
    // API_BASE_URL: 'http://localhost:8000/api/v1',  // 本地后端地址
    API_BASE_URL: 'http://42.194.134.223:8000/api/v1',  // 开发服务器
    WS_URL: 'ws://localhost:8000/ws',
    DEBUG: true
  },
  
  // 生产环境
  production: {
    API_BASE_URL: 'https://api.yourdomain.com/api/v1',  // 正式服务器
    WS_URL: 'wss://api.yourdomain.com/ws',
    DEBUG: false
  }
};

// 导出当前环境配置
module.exports = {
  ENV,
  ...config[ENV],
  
  // 通用配置
  VERSION: '1.0.0',                    // 小程序版本
  REQUEST_TIMEOUT: 30000,              // 请求超时时间(毫秒)
  
  // 碳减排系数
  CARBON_COEFFICIENT: 2.5,             // 1kg衣物 = 2.5kg CO2
  
  // 积分系数
  POINTS_COEFFICIENT: 10,              // 1kg CO2 = 10积分
  
  // 页面路径
  PAGES: {
    INDEX: '/pages/index/index',
    SCAN: '/pages/scan/scan',
    CLAIM: '/pages/claim/claim',
    CLAIM_SUCCESS: '/pages/claim-success/claim-success',
    ORDERS: '/pages/orders/orders',
    ORDER_DETAIL: '/pages/order-detail/order-detail',
    WALLET: '/pages/wallet/wallet',
    WITHDRAW: '/pages/withdraw/withdraw',
    PROFILE: '/pages/profile/profile',
    NEARBY: '/pages/nearby/nearby'
  }
};

