// pages/claim-success/claim-success.js
// 领取成功页面

const util = require('../../utils/util');

Page({
  data: {
    // 领取结果
    result: null,
    // 计算后的展示数据
    treesPlanted: '0',
    waterSaved: '0'
  },

  onLoad(options) {
    // 解析传递过来的数据
    if (options.data) {
      try {
        const result = JSON.parse(decodeURIComponent(options.data));
        // 计算环保数据
        const treesPlanted = (result.carbon_reduction / 20).toFixed(1);
        const waterSaved = Math.round(result.weight * 2500);
        
        // 预格式化显示数据
        const displayResult = {
          ...result,
          amountDisplay: util.formatMoney(result.amount),
          weightDisplay: result.weight ? Number(result.weight).toFixed(2) : '0.00',
          carbonDisplay: result.carbon_reduction ? Number(result.carbon_reduction).toFixed(2) : '0.00',
          walletBalanceDisplay: util.formatMoney(result.wallet_balance)
        };
        
        this.setData({ 
          result: displayResult,
          treesPlanted,
          waterSaved
        });
      } catch (e) {
        console.error('解析数据失败:', e);
      }
    }
  },

  // 查看订单详情
  viewOrderDetail() {
    const { result } = this.data;
    if (result && result.order_id) {
      wx.navigateTo({
        url: `/pages/order-detail/order-detail?id=${result.order_id}`
      });
    }
  },

  // 继续扫码
  continueScan() {
    wx.navigateBack();
  },

  // 返回首页
  goHome() {
    wx.switchTab({ url: '/pages/index/index' });
  },

  // 查看钱包
  goToWallet() {
    wx.navigateTo({ url: '/pages/wallet/wallet' });
  },

  // 分享
  onShareAppMessage() {
    return {
      title: '我在智能旧衣回收箱投递了旧衣物，一起来环保吧！',
      path: '/pages/index/index',
      imageUrl: '/images/share-cover.png'
    };
  },

  // 格式化金额
  formatMoney(amount) {
    return util.formatMoney(amount);
  }
});

