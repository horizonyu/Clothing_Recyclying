/**
 * 通用工具函数
 */

/**
 * 格式化日期
 * @param {Date|string|number} date 日期
 * @param {string} format 格式 YYYY-MM-DD HH:mm:ss
 * @returns {string}
 */
const formatDate = (date, format = 'YYYY-MM-DD HH:mm:ss') => {
  if (!date) return '';
  
  const d = new Date(date);
  
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hour = String(d.getHours()).padStart(2, '0');
  const minute = String(d.getMinutes()).padStart(2, '0');
  const second = String(d.getSeconds()).padStart(2, '0');
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hour)
    .replace('mm', minute)
    .replace('ss', second);
};

/**
 * 格式化金额
 * @param {number} amount 金额
 * @param {number} decimals 小数位数
 * @returns {string}
 */
const formatMoney = (amount, decimals = 2) => {
  if (amount === null || amount === undefined) return '0.00';
  return Number(amount).toFixed(decimals);
};

/**
 * 格式化重量
 * @param {number} weight 重量(kg)
 * @returns {string}
 */
const formatWeight = (weight) => {
  if (!weight) return '0';
  if (weight >= 1) {
    return weight.toFixed(2) + ' kg';
  } else {
    return (weight * 1000).toFixed(0) + ' g';
  }
};

/**
 * 格式化碳减排量
 * @param {number} carbon 碳减排量(kg)
 * @returns {string}
 */
const formatCarbon = (carbon) => {
  if (!carbon) return '0 kg';
  return carbon.toFixed(2) + ' kg CO₂';
};

/**
 * 获取订单状态文字
 * @param {number} status 状态码
 * @returns {object} { text, type }
 */
const getOrderStatusInfo = (status) => {
  const statusMap = {
    0: { text: '待领取', type: 'warning' },
    1: { text: '已领取', type: 'success' },
    2: { text: '已过期', type: 'danger' },
    3: { text: '异常', type: 'danger' }
  };
  return statusMap[status] || { text: '未知', type: '' };
};

/**
 * 防抖函数
 * @param {Function} fn 函数
 * @param {number} delay 延迟时间(ms)
 * @returns {Function}
 */
const debounce = (fn, delay = 300) => {
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
};

/**
 * 节流函数
 * @param {Function} fn 函数
 * @param {number} interval 间隔时间(ms)
 * @returns {Function}
 */
const throttle = (fn, interval = 300) => {
  let lastTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastTime >= interval) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
};

/**
 * 检查是否为空
 * @param {any} value 值
 * @returns {boolean}
 */
const isEmpty = (value) => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string' && value.trim() === '') return true;
  if (Array.isArray(value) && value.length === 0) return true;
  if (typeof value === 'object' && Object.keys(value).length === 0) return true;
  return false;
};

/**
 * 显示加载提示
 * @param {string} title 提示文字
 */
const showLoading = (title = '加载中...') => {
  wx.showLoading({ title, mask: true });
};

/**
 * 隐藏加载提示
 */
const hideLoading = () => {
  wx.hideLoading();
};

/**
 * 显示成功提示
 * @param {string} title 提示文字
 */
const showSuccess = (title) => {
  wx.showToast({ title, icon: 'success' });
};

/**
 * 显示错误提示
 * @param {string} title 提示文字
 */
const showError = (title) => {
  wx.showToast({ title, icon: 'none' });
};

/**
 * 显示确认弹窗
 * @param {object} options 配置
 * @returns {Promise<boolean>}
 */
const showConfirm = (options) => {
  return new Promise((resolve) => {
    wx.showModal({
      title: options.title || '提示',
      content: options.content || '',
      showCancel: options.showCancel !== false,
      cancelText: options.cancelText || '取消',
      confirmText: options.confirmText || '确定',
      success: (res) => {
        resolve(res.confirm);
      }
    });
  });
};

/**
 * 复制到剪贴板
 * @param {string} data 要复制的内容
 */
const copyToClipboard = (data) => {
  wx.setClipboardData({
    data,
    success: () => {
      wx.showToast({ title: '已复制', icon: 'success' });
    }
  });
};

/**
 * 拨打电话
 * @param {string} phoneNumber 电话号码
 */
const makePhoneCall = (phoneNumber) => {
  wx.makePhoneCall({ phoneNumber });
};

module.exports = {
  formatDate,
  formatMoney,
  formatWeight,
  formatCarbon,
  getOrderStatusInfo,
  debounce,
  throttle,
  isEmpty,
  showLoading,
  hideLoading,
  showSuccess,
  showError,
  showConfirm,
  copyToClipboard,
  makePhoneCall
};

