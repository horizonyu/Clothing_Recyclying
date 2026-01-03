// app.js
// 小程序入口文件

App({
  // 全局数据
  globalData: {
    userInfo: null,      // 用户信息
    token: null,         // 登录Token
    isLogin: false,      // 是否已登录
    systemInfo: null     // 系统信息
  },

  // 小程序启动时执行
  onLaunch() {
    console.log('小程序启动');
    
    // 获取系统信息
    this.getSystemInfo();
    
    // 检查登录状态
    this.checkLoginStatus();
  },

  // 获取系统信息
  getSystemInfo() {
    try {
      const systemInfo = wx.getSystemInfoSync();
      this.globalData.systemInfo = systemInfo;
      console.log('系统信息:', systemInfo);
    } catch (e) {
      console.error('获取系统信息失败:', e);
    }
  },

  // 检查登录状态
  checkLoginStatus() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    
    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
      this.globalData.isLogin = true;
      console.log('已登录用户:', userInfo.nickname || userInfo.user_id);
    } else {
      this.globalData.isLogin = false;
      console.log('用户未登录');
    }
  },

  // 微信登录
  async login() {
    return new Promise((resolve, reject) => {
      // 1. 获取微信登录code
      wx.login({
        success: async (res) => {
          if (res.code) {
            console.log('获取code成功:', res.code);
            
            try {
              // 2. 将code发送到后端换取token
              const userService = require('./services/user');
              const result = await userService.loginByWechat(res.code);
              
              // 3. 保存登录信息
              this.globalData.token = result.token;
              this.globalData.userInfo = result;
              this.globalData.isLogin = true;
              
              wx.setStorageSync('token', result.token);
              wx.setStorageSync('userInfo', result);
              
              console.log('登录成功:', result);
              resolve(result);
            } catch (e) {
              console.error('登录请求失败:', e);
              reject(e);
            }
          } else {
            console.error('获取code失败:', res.errMsg);
            reject(new Error(res.errMsg));
          }
        },
        fail: (err) => {
          console.error('wx.login失败:', err);
          reject(err);
        }
      });
    });
  },

  // 退出登录
  logout() {
    this.globalData.token = null;
    this.globalData.userInfo = null;
    this.globalData.isLogin = false;
    
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    
    console.log('已退出登录');
  },

  // 检查是否登录，未登录则执行登录
  async ensureLogin() {
    if (this.globalData.isLogin) {
      return this.globalData.userInfo;
    }
    return await this.login();
  }
});

