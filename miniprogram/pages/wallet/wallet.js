// pages/wallet/wallet.js
// 钱包页面

const app = getApp();
const userService = require('../../services/user');
const util = require('../../utils/util');

Page({
  data: {
    // 钱包信息
    balance: 0,
    frozenBalance: 0,
    
    // 交易记录
    records: [],
    page: 1,
    pageSize: 20,
    hasMore: true,
    loading: false
  },

  onLoad() {
    this.loadWalletInfo();
    this.loadRecords();
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadWalletInfo(),
      this.refreshRecords()
    ]).finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMoreRecords();
    }
  },

  // 加载钱包信息
  async loadWalletInfo() {
    try {
      const result = await userService.getWalletBalance();
      this.setData({
        balance: result.balance || 0,
        frozenBalance: result.frozen_balance || 0
      });
    } catch (e) {
      console.error('加载钱包信息失败:', e);
    }
  },

  // 加载交易记录
  async loadRecords() {
    this.setData({ loading: true });

    try {
      const result = await userService.getWalletRecords(1, this.data.pageSize);
      this.setData({
        records: result.items || [],
        page: 1,
        hasMore: (result.items || []).length >= this.data.pageSize,
        loading: false
      });
    } catch (e) {
      this.setData({ loading: false });
    }
  },

  // 刷新记录
  async refreshRecords() {
    try {
      const result = await userService.getWalletRecords(1, this.data.pageSize);
      this.setData({
        records: result.items || [],
        page: 1,
        hasMore: (result.items || []).length >= this.data.pageSize
      });
    } catch (e) {
      console.error('刷新记录失败:', e);
    }
  },

  // 加载更多
  async loadMoreRecords() {
    if (!this.data.hasMore || this.data.loading) return;

    this.setData({ loading: true });

    try {
      const nextPage = this.data.page + 1;
      const result = await userService.getWalletRecords(nextPage, this.data.pageSize);
      const newRecords = result.items || [];

      this.setData({
        records: [...this.data.records, ...newRecords],
        page: nextPage,
        hasMore: newRecords.length >= this.data.pageSize,
        loading: false
      });
    } catch (e) {
      this.setData({ loading: false });
    }
  },

  // 去提现
  goToWithdraw() {
    wx.navigateTo({ url: '/pages/withdraw/withdraw' });
  },

  // 获取交易类型文字
  getTypeText(type) {
    const typeMap = {
      'income': '回收收入',
      'withdraw': '提现',
      'refund': '退款'
    };
    return typeMap[type] || type;
  },

  // 格式化金额
  formatMoney(amount) {
    return util.formatMoney(amount);
  },

  // 格式化日期
  formatDate(date) {
    return util.formatDate(date, 'MM-DD HH:mm');
  }
});

