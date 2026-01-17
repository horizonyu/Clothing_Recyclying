// pages/profile-edit/profile-edit.js
// 个人信息编辑页面

const app = getApp();
const userService = require('../../services/user');
const util = require('../../utils/util');

Page({
  data: {
    userInfo: null,
    nickname: '',
    isSubmitting: false
  },

  onLoad() {
    this.loadUserInfo();
  },

  // 加载用户信息
  loadUserInfo() {
    const userInfo = app.globalData.userInfo;
    if (userInfo) {
      this.setData({
        userInfo: userInfo,
        nickname: userInfo.nickname || ''
      });
    }
  },

  // 昵称输入
  onNicknameInput(e) {
    this.setData({
      nickname: e.detail.value
    });
  },

  // 昵称输入完成（微信昵称键盘）
  onNicknameChange(e) {
    const nickname = e.detail.value;
    console.log('输入的昵称:', nickname);
    this.setData({
      nickname: nickname
    });
  },

  // 保存修改
  async saveProfile() {
    const { nickname, userInfo, isSubmitting } = this.data;
    
    if (isSubmitting) return;
    
    // 验证昵称
    const trimmedNickname = nickname.trim();
    if (!trimmedNickname) {
      util.showError('请输入昵称');
      return;
    }
    
    if (trimmedNickname.length > 20) {
      util.showError('昵称不能超过20个字符');
      return;
    }
    
    // 检查昵称是否有修改
    const hasNicknameChanged = trimmedNickname !== (userInfo.nickname || '');
    
    if (!hasNicknameChanged) {
      // 昵称没变，直接返回
      wx.navigateBack();
      return;
    }
    
    this.setData({ isSubmitting: true });
    
    try {
      util.showLoading('保存中...');
      
      // 只更新昵称
      const result = await userService.updateProfile({
        nickname: trimmedNickname
      });
      
      util.hideLoading();
      
      // 更新全局数据
      app.globalData.userInfo = {
        ...app.globalData.userInfo,
        nickname: result.nickname
      };
      
      // 更新本地存储
      wx.setStorageSync('userInfo', app.globalData.userInfo);
      
      wx.showToast({
        title: '保存成功',
        icon: 'success',
        duration: 1500,
        success: () => {
          setTimeout(() => {
            wx.navigateBack();
          }, 1500);
        }
      });
      
    } catch (e) {
      util.hideLoading();
      console.error('保存失败:', e);
      util.showError(e.message || '保存失败');
    } finally {
      this.setData({ isSubmitting: false });
    }
  },

  // 取消修改
  cancel() {
    wx.navigateBack();
  }
});
