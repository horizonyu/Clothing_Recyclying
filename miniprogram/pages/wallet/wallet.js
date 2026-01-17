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
    balanceDisplay: '0.00',
    frozenBalanceDisplay: '0.00',
    
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
      const balance = result.balance || 0;
      const frozenBalance = result.frozen_balance || 0;
      
      this.setData({
        balance: balance,
        frozenBalance: frozenBalance,
        // 预格式化显示数据
        balanceDisplay: this.formatMoneyValue(balance),
        frozenBalanceDisplay: this.formatMoneyValue(frozenBalance)
      });
    } catch (e) {
      console.error('加载钱包信息失败:', e);
    }
  },
  
  // 格式化金额值
  formatMoneyValue(amount) {
    if (amount === null || amount === undefined) return '0.00';
    return Number(amount).toFixed(2);
  },
  
  // 格式化日期值
  formatDateValue(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    return `${month}-${day} ${hour}:${minute}`;
  },
  
  // 获取交易类型文字
  getTypeTextValue(type) {
    const typeMap = {
      'income': '回收收入',
      'withdraw': '提现',
      'refund': '退款'
    };
    return typeMap[type] || type;
  },
  
  // 格式化记录列表用于显示
  formatRecordsForDisplay(records) {
    return records.map(item => ({
      ...item,
      typeText: this.getTypeTextValue(item.type),
      timeDisplay: this.formatDateValue(item.created_at),
      amountDisplay: this.formatMoneyValue(item.amount),
      isIncome: item.type === 'income' || item.type === 'refund'
    }));
  },

  // 加载交易记录
  async loadRecords() {
    this.setData({ loading: true });

    try {
      const result = await userService.getWalletRecords(1, this.data.pageSize);
      const items = result.items || [];
      
      this.setData({
        records: this.formatRecordsForDisplay(items),
        page: 1,
        hasMore: items.length >= this.data.pageSize,
        loading: false
      });
    } catch (e) {
      console.error('加载交易记录失败:', e);
      this.setData({ loading: false });
    }
  },

  // 刷新记录
  async refreshRecords() {
    try {
      const result = await userService.getWalletRecords(1, this.data.pageSize);
      const items = result.items || [];
      
      this.setData({
        records: this.formatRecordsForDisplay(items),
        page: 1,
        hasMore: items.length >= this.data.pageSize
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
      const newItems = result.items || [];
      const formattedNewItems = this.formatRecordsForDisplay(newItems);

      this.setData({
        records: [...this.data.records, ...formattedNewItems],
        page: nextPage,
        hasMore: newItems.length >= this.data.pageSize,
        loading: false
      });
    } catch (e) {
      console.error('加载更多失败:', e);
      this.setData({ loading: false });
    }
  },

  // 去提现
  goToWithdraw() {
    wx.navigateTo({ url: '/pages/withdraw/withdraw' });
  }
});

