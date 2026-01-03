/**
 * 用户服务
 * 处理用户相关的API请求
 */

const request = require('../utils/request');

/**
 * 微信登录
 * @param {string} code 微信登录code
 * @returns {Promise<object>} 用户信息和token
 */
const loginByWechat = (code) => {
  return request.post('/user/login/wechat', { code });
};

/**
 * 获取用户信息
 * @returns {Promise<object>}
 */
const getUserProfile = () => {
  return request.get('/user/profile');
};

/**
 * 更新用户信息
 * @param {object} data 用户信息
 * @returns {Promise<object>}
 */
const updateProfile = (data) => {
  return request.put('/user/profile', data);
};

/**
 * 绑定手机号
 * @param {string} encryptedData 加密数据
 * @param {string} iv 初始向量
 * @returns {Promise<object>}
 */
const bindPhone = (encryptedData, iv) => {
  return request.post('/user/bindphone', { encrypted_data: encryptedData, iv });
};

/**
 * 实名认证
 * @param {string} realName 真实姓名
 * @param {string} idCard 身份证号
 * @returns {Promise<object>}
 */
const verifyIdentity = (realName, idCard) => {
  return request.post('/user/verify', { 
    real_name: realName, 
    id_card: idCard 
  });
};

/**
 * 获取钱包余额
 * @returns {Promise<object>}
 */
const getWalletBalance = () => {
  return request.get('/wallet/balance');
};

/**
 * 获取交易记录
 * @param {number} page 页码
 * @param {number} pageSize 每页数量
 * @returns {Promise<object>}
 */
const getWalletRecords = (page = 1, pageSize = 20) => {
  return request.get('/wallet/records', { page, page_size: pageSize });
};

/**
 * 申请提现
 * @param {number} amount 提现金额
 * @param {string} channel 提现渠道 wechat/alipay
 * @returns {Promise<object>}
 */
const withdraw = (amount, channel = 'wechat') => {
  return request.post('/wallet/withdraw', { amount, channel });
};

/**
 * 获取积分余额
 * @returns {Promise<object>}
 */
const getPointsBalance = () => {
  return request.get('/points/balance');
};

/**
 * 获取积分记录
 * @param {number} page 页码
 * @param {number} pageSize 每页数量
 * @returns {Promise<object>}
 */
const getPointsRecords = (page = 1, pageSize = 20) => {
  return request.get('/points/records', { page, page_size: pageSize });
};

module.exports = {
  loginByWechat,
  getUserProfile,
  updateProfile,
  bindPhone,
  verifyIdentity,
  getWalletBalance,
  getWalletRecords,
  withdraw,
  getPointsBalance,
  getPointsRecords
};

