// pages/profile/profile.js
// 个人中心页面

const app = getApp();
const userService = require('../../services/user');
const util = require('../../utils/util');

Page({
  data: {
    // 用户信息
    userInfo: null,
    isLogin: false,
    
    // 钱包信息
    wallet: {
      balance: 0,
      points: 0
    },
    
    // 统计信息
    stats: {
      totalWeight: 0,
      totalCarbon: 0,
      totalCount: 0
    }
  },

  onLoad() {
    this.initPage();
  },

  onShow() {
    // 每次显示时刷新数据
    if (app.globalData.isLogin) {
      this.loadUserData();
    }
  },

  // 初始化页面
  async initPage() {
    if (app.globalData.isLogin) {
      this.setData({
        isLogin: true,
        userInfo: app.globalData.userInfo
      });
      await this.loadUserData();
    }
  },

  // 加载用户数据
  async loadUserData() {
    try {
      const [walletRes, profileRes] = await Promise.all([
        userService.getWalletBalance(),
        userService.getUserProfile()
      ]);

      this.setData({
        wallet: {
          balance: walletRes.balance || 0,
          points: walletRes.points || 0
        },
        stats: {
          totalWeight: profileRes.total_weight || 0,
          totalCarbon: profileRes.total_carbon || 0,
          totalCount: profileRes.total_count || 0
        },
        userInfo: {
          ...this.data.userInfo,
          ...profileRes
        }
      });
    } catch (e) {
      console.error('加载用户数据失败:', e);
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
      await this.loadUserData();
    } catch (e) {
      util.hideLoading();
      util.showError('登录失败');
    }
  },

  // 跳转到钱包
  goToWallet() {
    if (!this.data.isLogin) {
      return this.handleLogin();
    }
    wx.navigateTo({ url: '/pages/wallet/wallet' });
  },

  // 跳转到投递记录
  goToOrders() {
    if (!this.data.isLogin) {
      return this.handleLogin();
    }
    wx.switchTab({ url: '/pages/orders/orders' });
  },

  // 跳转到提现
  goToWithdraw() {
    if (!this.data.isLogin) {
      return this.handleLogin();
    }
    wx.navigateTo({ url: '/pages/withdraw/withdraw' });
  },

  // 联系客服
  contactService() {
    wx.makePhoneCall({ phoneNumber: '400-XXX-XXXX' });
  },

  // 关于我们
  showAbout() {
    wx.showModal({
      title: '关于我们',
      content: '智能旧衣回收箱，让环保更简单。我们致力于回收再利用旧衣物，减少碳排放，保护地球环境。',
      showCancel: false
    });
  },

  // 退出登录
  async logout() {
    const confirm = await util.showConfirm({
      title: '提示',
      content: '确定要退出登录吗？'
    });

    if (confirm) {
      app.logout();
      this.setData({
        isLogin: false,
        userInfo: null,
        wallet: { balance: 0, points: 0 },
        stats: { totalWeight: 0, totalCarbon: 0, totalCount: 0 }
      });
      util.showSuccess('已退出登录');
    }
  },

  // 格式化金额
  formatMoney(amount) {
    return util.formatMoney(amount);
  }
});

