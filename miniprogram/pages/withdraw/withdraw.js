// pages/withdraw/withdraw.js
// 提现页面

const app = getApp();
const userService = require('../../services/user');
const util = require('../../utils/util');

Page({
  data: {
    // 可提现余额
    availableBalance: 0,
    availableBalanceDisplay: '0.00',
    
    // 提现金额
    amount: '',
    
    // 提现渠道
    channel: 'wechat',
    
    // 最小提现金额
    minAmount: 1,
    
    // 提交中
    submitting: false
  },

  onLoad() {
    this.loadBalance();
  },

  // 加载余额
  async loadBalance() {
    try {
      const result = await userService.getWalletBalance();
      const balance = result.available_balance || result.balance || 0;
      this.setData({
        availableBalance: balance,
        availableBalanceDisplay: Number(balance).toFixed(2)
      });
    } catch (e) {
      console.error('加载余额失败:', e);
    }
  },

  // 输入金额
  onAmountInput(e) {
    let value = e.detail.value;
    // 限制两位小数
    if (value.includes('.')) {
      const parts = value.split('.');
      if (parts[1] && parts[1].length > 2) {
        value = parts[0] + '.' + parts[1].slice(0, 2);
      }
    }
    this.setData({ amount: value });
  },

  // 提现全部
  withdrawAll() {
    this.setData({
      amount: this.data.availableBalance.toString()
    });
  },

  // 切换渠道
  switchChannel(e) {
    const channel = e.currentTarget.dataset.channel;
    this.setData({ channel });
  },

  // 提交提现
  async submitWithdraw() {
    const { amount, availableBalance, minAmount, channel, submitting } = this.data;

    if (submitting) return;

    // 验证金额
    const amountNum = parseFloat(amount);
    if (!amount || isNaN(amountNum)) {
      util.showError('请输入提现金额');
      return;
    }

    if (amountNum < minAmount) {
      util.showError(`最低提现金额为${minAmount}元`);
      return;
    }

    if (amountNum > availableBalance) {
      util.showError('提现金额超过可用余额');
      return;
    }

    // 确认提现
    const confirm = await util.showConfirm({
      title: '确认提现',
      content: `确定提现 ¥${amountNum.toFixed(2)} 到${channel === 'wechat' ? '微信' : '支付宝'}吗？`
    });

    if (!confirm) return;

    this.setData({ submitting: true });

    try {
      util.showLoading('提交中...');
      await userService.withdraw(amountNum, channel);
      util.hideLoading();
      
      wx.showModal({
        title: '提现成功',
        content: '提现申请已提交，资金将即时到账，请查看微信零钱',
        showCancel: false,
        success: () => {
          // 刷新钱包余额
          this.loadBalance();
          wx.navigateBack();
        }
      });
    } catch (e) {
      util.hideLoading();
      util.showError(e.message || '提现失败');
      this.setData({ submitting: false });
    }
  }
});

