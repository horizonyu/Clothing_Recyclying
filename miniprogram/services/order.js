/**
 * 订单服务
 * 处理订单相关的API请求
 */

const request = require('../utils/request');

/**
 * 扫码解析投递凭证
 * @param {string} qrcodeData Base64编码的二维码内容
 * @returns {Promise<object>} 订单信息
 */
const scanQrcode = (qrcodeData) => {
  return request.post('/order/scan', { qrcode_data: qrcodeData });
};

/**
 * 领取订单金额
 * @param {string} orderId 订单ID
 * @returns {Promise<object>} 领取结果
 */
const claimOrder = (orderId) => {
  return request.post(`/order/${orderId}/claim`);
};

/**
 * 获取订单列表
 * @param {object} params 查询参数
 * @param {number} params.page 页码
 * @param {number} params.pageSize 每页数量
 * @param {number} params.status 状态筛选
 * @returns {Promise<object>}
 */
const getOrderList = (params = {}) => {
  const { page = 1, pageSize = 20, status } = params;
  const data = { page, page_size: pageSize };
  // 只有当 status 是有效数字时才添加到请求参数
  if (status !== undefined && status !== null) {
    data.status = status;
  }
  return request.get('/order/list', data);
};

/**
 * 获取订单详情
 * @param {string} orderId 订单ID
 * @returns {Promise<object>}
 */
const getOrderDetail = (orderId) => {
  return request.get(`/order/${orderId}/detail`);
};

/**
 * 追踪衣物去向
 * @param {string} orderId 订单ID
 * @returns {Promise<object>}
 */
const trackOrder = (orderId) => {
  return request.get(`/order/${orderId}/track`);
};

/**
 * 获取订单统计
 * @returns {Promise<object>}
 */
const getOrderStats = () => {
  return request.get('/order/stats');
};

module.exports = {
  scanQrcode,
  claimOrder,
  getOrderList,
  getOrderDetail,
  trackOrder,
  getOrderStats
};

