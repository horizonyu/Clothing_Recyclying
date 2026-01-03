// pages/order-detail/order-detail.js
// 订单详情页面

const orderService = require('../../services/order');
const util = require('../../utils/util');

Page({
  data: {
    orderId: '',
    order: null,
    loading: true
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ orderId: options.id });
      this.loadOrderDetail(options.id);
    }
  },

  // 加载订单详情
  async loadOrderDetail(orderId) {
    this.setData({ loading: true });

    try {
      const order = await orderService.getOrderDetail(orderId);
      this.setData({ order, loading: false });
    } catch (e) {
      util.showError('加载失败');
      this.setData({ loading: false });
    }
  },

  // 复制订单号
  copyOrderId() {
    util.copyToClipboard(this.data.orderId);
  },

  // 查看去向追踪
  viewTrack() {
    // TODO: 跳转到去向追踪页面
    util.showError('功能开发中');
  },

  // 获取状态信息
  getStatusInfo(status) {
    return util.getOrderStatusInfo(status);
  },

  // 格式化金额
  formatMoney(amount) {
    return util.formatMoney(amount);
  },

  // 格式化日期
  formatDate(date) {
    return util.formatDate(date, 'YYYY-MM-DD HH:mm:ss');
  }
});

