import request from '@/utils/request'

// 登录
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

// 退出登录
export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

// 获取用户信息
export function getProfile() {
  return request({
    url: '/auth/profile',
    method: 'get'
  })
}

// 获取统计数据
export function getDashboardStats(params) {
  return request({
    url: '/dashboard/stats',
    method: 'get',
    params
  })
}

// ===== 设备管理 =====

// 获取设备列表
export function getDeviceList(params) {
  return request({
    url: '/device/list',
    method: 'get',
    params
  })
}

// 获取设备详情
export function getDeviceDetail(id) {
  return request({
    url: `/device/detail/${id}`,
    method: 'get'
  })
}

// 获取设备统计概览
export function getDeviceStats() {
  return request({
    url: '/device/stats',
    method: 'get'
  })
}

// 更新设备
export function updateDevice(id, data) {
  return request({
    url: `/device/${id}`,
    method: 'put',
    data
  })
}

// 获取设备摄像头图片历史
export function getDeviceCameraImages(deviceId, params) {
  return request({
    url: `/device/${deviceId}/camera-images`,
    method: 'get',
    params
  })
}

// 主动查询设备状态（下发 query_device_status 命令）
export function queryDeviceStatus(deviceId) {
  return request({
    url: '/device/query-status',
    method: 'post',
    params: { device_id: deviceId }
  })
}

// ===== 订单管理 =====

// 获取订单列表
export function getOrderList(params) {
  return request({
    url: '/order/list',
    method: 'get',
    params
  })
}

// 获取订单详情
export function getOrderDetail(id) {
  return request({
    url: `/order/${id}`,
    method: 'get'
  })
}

// 审核订单
export function auditOrder(id, data) {
  return request({
    url: `/order/${id}/audit`,
    method: 'post',
    data
  })
}

// ===== 用户管理 =====

// 获取用户列表
export function getUserList(params) {
  return request({
    url: '/user/list',
    method: 'get',
    params
  })
}

// 获取用户详情
export function getUserDetail(id) {
  return request({
    url: `/user/${id}`,
    method: 'get'
  })
}

// 更新用户状态
export function updateUserStatus(id, data) {
  return request({
    url: `/user/${id}/status`,
    method: 'put',
    data
  })
}

// ===== 财务管理 =====

// 获取提现列表
export function getWithdrawList(params) {
  return request({
    url: '/finance/withdraw/list',
    method: 'get',
    params
  })
}

// 审核提现
export function auditWithdraw(id, data) {
  return request({
    url: `/finance/withdraw/${id}/audit`,
    method: 'post',
    data
  })
}
