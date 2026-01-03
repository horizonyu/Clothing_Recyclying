/**
 * 网络请求封装
 * 统一处理请求、响应、错误
 */

const config = require('../config/index');

class Request {
  constructor() {
    this.baseUrl = config.API_BASE_URL;
    this.timeout = config.REQUEST_TIMEOUT;
  }

  /**
   * 发起请求
   * @param {Object} options 请求配置
   * @returns {Promise}
   */
  request(options) {
    return new Promise((resolve, reject) => {
      // 获取Token
      const token = wx.getStorageSync('token');
      
      // 构建请求头
      const header = {
        'Content-Type': 'application/json',
        ...options.header
      };
      
      // 添加认证Token
      if (token) {
        header['Authorization'] = `Bearer ${token}`;
      }

      // 打印请求信息（调试用）
      if (config.DEBUG) {
        console.log('📤 Request:', {
          url: `${this.baseUrl}${options.url}`,
          method: options.method || 'GET',
          data: options.data,
          header
        });
      }

      // 发起请求
      wx.request({
        url: `${this.baseUrl}${options.url}`,
        method: options.method || 'GET',
        data: options.data,
        header,
        timeout: this.timeout,
        
        success: (res) => {
          // 打印响应信息（调试用）
          if (config.DEBUG) {
            console.log('📥 Response [' + res.statusCode + ']:', res.data);
          }

          // 处理HTTP状态码
          if (res.statusCode === 200) {
            // 处理业务状态码
            if (res.data.code === 0) {
              resolve(res.data.data);
            } else {
              // 业务错误
              this.handleBusinessError(res.data);
              reject(res.data);
            }
          } else if (res.statusCode === 401) {
            // Token过期，需要重新登录
            this.handleUnauthorized();
            reject({ code: 401, message: '登录已过期，请重新登录' });
          } else if (res.statusCode === 403) {
            reject({ code: 403, message: '没有访问权限' });
          } else if (res.statusCode === 404) {
            reject({ code: 404, message: '请求的资源不存在' });
          } else if (res.statusCode >= 500) {
            reject({ code: res.statusCode, message: '服务器错误，请稍后重试' });
          } else {
            // 400 等其他错误 - FastAPI 返回的错误在 detail 字段
            const detail = res.data.detail;
            let errorMsg = '请求失败';
            let errorCode = res.statusCode;
            
            if (detail) {
              if (typeof detail === 'object') {
                errorCode = detail.code || res.statusCode;
                errorMsg = detail.message || JSON.stringify(detail);
              } else {
                errorMsg = detail;
              }
            } else if (res.data.message) {
              errorMsg = res.data.message;
            }
            
            console.error('❌ HTTP Error:', res.statusCode, detail || res.data);
            reject({ code: errorCode, message: errorMsg });
          }
        },
        
        fail: (err) => {
          console.error('❌ Request failed:', err);
          
          // 网络错误处理
          if (err.errMsg.includes('timeout')) {
            wx.showToast({ title: '请求超时', icon: 'none' });
          } else if (err.errMsg.includes('fail')) {
            wx.showToast({ title: '网络连接失败', icon: 'none' });
          }
          
          reject({ code: -1, message: err.errMsg || '网络错误' });
        }
      });
    });
  }

  /**
   * GET请求
   */
  get(url, data = {}) {
    return this.request({ url, method: 'GET', data });
  }

  /**
   * POST请求
   */
  post(url, data = {}) {
    return this.request({ url, method: 'POST', data });
  }

  /**
   * PUT请求
   */
  put(url, data = {}) {
    return this.request({ url, method: 'PUT', data });
  }

  /**
   * DELETE请求
   */
  delete(url, data = {}) {
    return this.request({ url, method: 'DELETE', data });
  }

  /**
   * 处理业务错误
   */
  handleBusinessError(data) {
    const errorMessages = {
      10001: '二维码无效或已过期',
      10002: '设备不存在',
      10003: '订单已被领取',
      10004: '二维码已过期',
      10005: '请先完成实名认证',
      10006: '数据格式错误',
      10007: '签名验证失败',
      20001: '余额不足',
      20002: '提现金额低于最小限额',
      20003: '超过单日提现上限'
    };
    
    const message = errorMessages[data.code] || data.message || '操作失败';
    wx.showToast({ title: message, icon: 'none', duration: 2000 });
  }

  /**
   * 处理401未授权
   */
  handleUnauthorized() {
    // 清除本地登录信息
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    
    // 更新全局状态
    const app = getApp();
    if (app) {
      app.globalData.isLogin = false;
      app.globalData.token = null;
      app.globalData.userInfo = null;
    }
    
    // 提示用户
    wx.showModal({
      title: '提示',
      content: '登录已过期，请重新登录',
      showCancel: false,
      success: () => {
        // 跳转到首页重新登录
        wx.switchTab({ url: '/pages/index/index' });
      }
    });
  }
}

// 导出单例
module.exports = new Request();

