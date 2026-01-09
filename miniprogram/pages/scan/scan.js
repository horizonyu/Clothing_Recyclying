// pages/scan/scan.js
// 扫码页面 - 核心功能页面

const app = getApp();
const orderService = require('../../services/order');
const util = require('../../utils/util');
const config = require('../../config/index');

Page({
  data: {
    // 扫码状态
    scanning: false,
    
    // 订单信息
    orderInfo: null,
    
    // 显示领取弹窗
    showClaimModal: false,
    
    // 领取中
    claiming: false
  },

  onLoad() {
    // 检查登录状态
    this.checkLogin();
  },

  onShow() {
    // 只重置扫码状态，不重置弹窗状态
    // 否则扫码返回后弹窗会被关闭
    this.setData({
      scanning: false
    });
  },

  // 检查登录状态
  async checkLogin() {
    if (!app.globalData.isLogin) {
      try {
        await app.login();
      } catch (e) {
        console.log('登录失败，用户可以先扫码');
      }
    }
  },

  // 开始扫码
  startScan() {
    if (this.data.scanning) return;
    
    this.setData({ scanning: true });
    
    wx.scanCode({
      onlyFromCamera: false,  // 允许从相册选择
      scanType: ['qrCode'],   // 只扫二维码
      
      success: async (res) => {
        console.log('扫码结果:', res);
        
        try {
          // 获取二维码内容
          const qrcodeData = res.result;
          
          // 显示加载
          util.showLoading('解析中...');
          
          // 调用后端接口解析二维码
          const orderInfo = await orderService.scanQrcode(qrcodeData);
          
          util.hideLoading();
          
          // 格式化数据用于显示
          const displayInfo = {
            ...orderInfo,
            weightDisplay: orderInfo.weight ? Number(orderInfo.weight).toFixed(2) : '0.00',
            unitPriceDisplay: orderInfo.unit_price ? Number(orderInfo.unit_price).toFixed(2) : '0.00',
            amountDisplay: orderInfo.amount ? Number(orderInfo.amount).toFixed(2) : '0.00',
            carbonDisplay: orderInfo.carbon_reduction ? Number(orderInfo.carbon_reduction).toFixed(2) : '0.00'
          };
          
          // 保存订单信息，显示弹窗
          this.setData({
            orderInfo: displayInfo,
            showClaimModal: true
          });
          
        } catch (e) {
          util.hideLoading();
          
          // 打印详细错误信息（调试用）
          console.error('❌ 扫码处理失败:', e);
          console.error('错误码:', e.code);
          console.error('错误信息:', e.message);
          
          // 根据错误码显示不同提示
          if (e.code === 10001) {
            util.showError('二维码无效或已过期');
          } else if (e.code === 10003) {
            util.showError('该订单已被领取');
          } else if (e.code === 10004) {
            util.showError('二维码已过期');
          } else if (e.code === 401) {
            util.showError('请先登录');
          } else {
            util.showError(e.message || '解析失败');
          }
        }
      },
      
      fail: (err) => {
        console.log('扫码取消或失败:', err);
        // 用户取消不提示错误
        if (err.errMsg && !err.errMsg.includes('cancel')) {
          util.showError('扫码失败');
        }
      },
      
      complete: () => {
        this.setData({ scanning: false });
      }
    });
  },

  // 确认领取
  async confirmClaim() {
    const { orderInfo, claiming } = this.data;
    
    if (claiming || !orderInfo) return;
    
    // 检查登录状态
    if (!app.globalData.isLogin) {
      try {
        util.showLoading('登录中...');
        await app.login();
        util.hideLoading();
      } catch (e) {
        util.hideLoading();
        util.showError('请先登录');
        return;
      }
    }
    
    this.setData({ claiming: true });
    
    try {
      util.showLoading('领取中...');
      
      // 调用领取接口
      const result = await orderService.claimOrder(orderInfo.order_id);
      
      util.hideLoading();
      
      // 关闭弹窗
      this.setData({
        showClaimModal: false,
        orderInfo: null,
        claiming: false
      });
      
      // 跳转到领取成功页面
      const resultStr = encodeURIComponent(JSON.stringify(result));
      wx.navigateTo({
        url: `/pages/claim-success/claim-success?data=${resultStr}`
      });
      
    } catch (e) {
      util.hideLoading();
      this.setData({ claiming: false });
      
      if (e.code === 10003) {
        util.showError('订单已被领取');
        this.closeModal();
      } else if (e.code === 10005) {
        // 需要实名认证
        wx.showModal({
          title: '提示',
          content: '提现需要先完成实名认证，是否前往认证？',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/profile/verify' });
            }
          }
        });
      } else {
        util.showError(e.message || '领取失败');
      }
    }
  },

  // 关闭弹窗
  closeModal() {
    this.setData({
      showClaimModal: false,
      orderInfo: null
    });
  },

  // 阻止弹窗背景滚动
  preventTouchMove() {
    return false;
  },

  // 格式化金额
  formatMoney(amount) {
    return util.formatMoney(amount);
  },

  // 格式化重量
  formatWeight(weight) {
    if (!weight) return '0';
    return Number(weight).toFixed(2);
  },

  // 格式化碳减排
  formatCarbon(carbon) {
    if (!carbon) return '0';
    return Number(carbon).toFixed(2);
  }
});

