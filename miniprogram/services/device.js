/**
 * 设备服务
 * 处理设备相关的API请求
 */

const request = require('../utils/request');

/**
 * 获取附近回收箱
 * @param {number} longitude 经度
 * @param {number} latitude 纬度
 * @param {number} radius 半径(米)
 * @returns {Promise<Array>}
 */
const getNearbyDevices = (longitude, latitude, radius = 5000) => {
  return request.get('/device/nearby', { longitude, latitude, radius });
};

/**
 * 获取设备详情
 * @param {string} deviceId 设备ID
 * @returns {Promise<object>}
 */
const getDeviceDetail = (deviceId) => {
  return request.get(`/device/${deviceId}/info`);
};

/**
 * 搜索设备
 * @param {string} keyword 关键词(地址/小区名)
 * @returns {Promise<Array>}
 */
const searchDevices = (keyword) => {
  return request.get('/device/search', { keyword });
};

module.exports = {
  getNearbyDevices,
  getDeviceDetail,
  searchDevices
};

