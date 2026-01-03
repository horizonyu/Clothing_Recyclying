// pages/orders/orders.js
// 订单列表页面

const app = getApp();
const orderService = require('../../services/order');
const util = require('../../utils/util');

Page({
  data: {
    // 订单列表
    orders: [],
    
    // 分页
    page: 1,
    pageSize: 20,
    hasMore: true,
    
    // 状态筛选 (null=全部, 0=待领取, 1=已领取)
    currentStatus: null,
    
    // 加载状态
    loading: false,
    refreshing: false
  },

  onLoad() {
    this.loadOrders();
  },

  onShow() {
    // 如果已登录，刷新列表
    if (app.globalData.isLogin && this.data.orders.length > 0) {
      this.refreshOrders();
    }
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.refreshOrders();
  },

  // 上拉加载更多
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore();
    }
  },

  // 加载订单列表
  async loadOrders() {
    if (!app.globalData.isLogin) {
      try {
        await app.login();
      } catch (e) {
        util.showError('请先登录');
        return;
      }
    }

    this.setData({ loading: true });

    try {
      const result = await orderService.getOrderList({
        page: 1,
        pageSize: this.data.pageSize,
        status: this.data.currentStatus
      });

      this.setData({
        orders: result.items || [],
        page: 1,
        hasMore: (result.items || []).length >= this.data.pageSize,
        loading: false
      });
    } catch (e) {
      console.error('加载订单失败:', e);
      this.setData({ loading: false });
    }
  },

  // 刷新订单
  async refreshOrders() {
    this.setData({ refreshing: true, page: 1 });

    try {
      const result = await orderService.getOrderList({
        page: 1,
        pageSize: this.data.pageSize,
        status: this.data.currentStatus
      });

      this.setData({
        orders: result.items || [],
        hasMore: (result.items || []).length >= this.data.pageSize,
        refreshing: false
      });
    } catch (e) {
      this.setData({ refreshing: false });
    }

    wx.stopPullDownRefresh();
  },

  // 加载更多
  async loadMore() {
    if (!this.data.hasMore || this.data.loading) return;

    this.setData({ loading: true });

    try {
      const nextPage = this.data.page + 1;
      const result = await orderService.getOrderList({
        page: nextPage,
        pageSize: this.data.pageSize,
        status: this.data.currentStatus
      });

      const newOrders = result.items || [];
      this.setData({
        orders: [...this.data.orders, ...newOrders],
        page: nextPage,
        hasMore: newOrders.length >= this.data.pageSize,
        loading: false
      });
    } catch (e) {
      this.setData({ loading: false });
    }
  },

  // 切换状态筛选
  switchStatus(e) {
    const status = e.currentTarget.dataset.status;
    if (status === this.data.currentStatus) return;

    this.setData({
      currentStatus: status,
      orders: [],
      page: 1,
      hasMore: true
    });

    this.loadOrders();
  },

  // 查看订单详情
  viewDetail(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/order-detail/order-detail?id=${orderId}`
    });
  },

  // 获取状态信息
  getStatusInfo(status) {
    return util.getOrderStatusInfo(status);
  },

  // 格式化日期
  formatDate(date) {
    return util.formatDate(date, 'YYYY-MM-DD HH:mm');
  },

  // 格式化金额
  formatMoney(amount) {
    return util.formatMoney(amount);
  }
});

