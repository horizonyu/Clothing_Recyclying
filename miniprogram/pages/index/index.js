// pages/index/index.js
// 首页

const app = getApp();
const userService = require('../../services/user');
const orderService = require('../../services/order');
const util = require('../../utils/util');

Page({
  data: {
    // 用户信息
    userInfo: null,
    isLogin: false,
    
    // 统计数据
    stats: {
      totalWeight: 0,       // 累计投递重量
      totalAmount: 0,       // 累计收益
      totalCarbon: 0,       // 累计碳减排
      totalCount: 0         // 累计投递次数
    },
    
    // 钱包余额
    balance: 0,
    
    // 加载状态
    loading: true
  },

  onLoad() {
    this.initPage();
  },

  onShow() {
    // 每次显示页面时刷新数据
    if (app.globalData.isLogin) {
      this.loadData();
    }
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadData().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  // 初始化页面
  async initPage() {
    // 检查登录状态
    if (app.globalData.isLogin) {
      this.setData({
        isLogin: true,
        userInfo: app.globalData.userInfo
      });
      await this.loadData();
    } else {
      // 尝试自动登录
      try {
        const userInfo = await app.login();
        this.setData({
          isLogin: true,
          userInfo
        });
        await this.loadData();
      } catch (e) {
        console.log('自动登录失败，等待用户手动登录');
        this.setData({ loading: false });
      }
    }
  },

  // 加载数据
  async loadData() {
    this.setData({ loading: true });
    
    try {
      // 并行请求多个接口
      const [walletRes, statsRes] = await Promise.all([
        userService.getWalletBalance(),
        orderService.getOrderStats()
      ]);
      
      this.setData({
        balance: walletRes.balance || 0,
        stats: {
          totalWeight: statsRes.total_weight || 0,
          totalAmount: statsRes.total_amount || 0,
          totalCarbon: statsRes.total_carbon || 0,
          totalCount: statsRes.total_count || 0
        },
        loading: false
      });
    } catch (e) {
      console.error('加载数据失败:', e);
      this.setData({ loading: false });
    }
  },

  // 用户登录
  async handleLogin() {
    try {
      util.showLoading('登录中...');
      const userInfo = await app.login();
      this.setData({
        isLogin: true,
        userInfo
      });
      util.hideLoading();
      util.showSuccess('登录成功');
      await this.loadData();
    } catch (e) {
      util.hideLoading();
      util.showError('登录失败');
    }
  },

  // 跳转到扫码页面
  goToScan() {
    wx.switchTab({ url: '/pages/scan/scan' });
  },

  // 跳转到附近回收箱
  goToNearby() {
    wx.navigateTo({ url: '/pages/nearby/nearby' });
  },

  // 跳转到钱包
  goToWallet() {
    if (!this.data.isLogin) {
      return this.handleLogin();
    }
    wx.navigateTo({ url: '/pages/wallet/wallet' });
  },

  // 跳转到订单列表
  goToOrders() {
    if (!this.data.isLogin) {
      return this.handleLogin();
    }
    wx.switchTab({ url: '/pages/orders/orders' });
  },

  // 格式化重量
  formatWeight(weight) {
    return util.formatWeight(weight);
  },

  // 格式化金额
  formatMoney(amount) {
    return util.formatMoney(amount);
  }
});

