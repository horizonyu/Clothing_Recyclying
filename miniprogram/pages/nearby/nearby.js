// pages/nearby/nearby.js
// 附近回收箱页面

const deviceService = require('../../services/device');
const util = require('../../utils/util');

Page({
  data: {
    // 当前位置
    latitude: 0,
    longitude: 0,
    
    // 设备列表
    devices: [],
    
    // 地图标记
    markers: [],
    
    // 加载状态
    loading: true,
    
    // 是否显示列表视图
    showList: true
  },

  onLoad() {
    this.getLocation();
  },

  // 获取当前位置
  getLocation() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          latitude: res.latitude,
          longitude: res.longitude
        });
        this.loadNearbyDevices();
      },
      fail: (err) => {
        console.error('获取位置失败:', err);
        util.showError('获取位置失败');
        this.setData({ loading: false });
        
        // 使用默认位置（北京）
        this.setData({
          latitude: 39.9042,
          longitude: 116.4074
        });
        this.loadNearbyDevices();
      }
    });
  },

  // 加载附近设备
  async loadNearbyDevices() {
    this.setData({ loading: true });

    try {
      const devices = await deviceService.getNearbyDevices(
        this.data.longitude,
        this.data.latitude,
        5000  // 5公里范围
      );

      // 生成地图标记
      const markers = devices.map((device, index) => ({
        id: index,
        latitude: device.latitude,
        longitude: device.longitude,
        title: device.name,
        iconPath: '/images/marker.png',
        width: 30,
        height: 40,
        callout: {
          content: device.name,
          display: 'ALWAYS',
          fontSize: 12,
          padding: 5,
          borderRadius: 5
        }
      }));

      this.setData({
        devices,
        markers,
        loading: false
      });
    } catch (e) {
      console.error('加载设备失败:', e);
      this.setData({ loading: false });
    }
  },

  // 切换视图
  toggleView() {
    this.setData({
      showList: !this.data.showList
    });
  },

  // 刷新位置
  refreshLocation() {
    this.getLocation();
  },

  // 点击设备
  onDeviceTap(e) {
    const index = e.currentTarget.dataset.index;
    const device = this.data.devices[index];
    
    // 移动地图到该位置
    this.setData({
      latitude: device.latitude,
      longitude: device.longitude,
      showList: false
    });
  },

  // 导航到设备
  navigateTo(e) {
    const index = e.currentTarget.dataset.index;
    const device = this.data.devices[index];
    
    wx.openLocation({
      latitude: device.latitude,
      longitude: device.longitude,
      name: device.name,
      address: device.address,
      scale: 18
    });
  },

  // 点击地图标记
  onMarkerTap(e) {
    const markerId = e.markerId;
    const device = this.data.devices[markerId];
    
    if (device) {
      this.showDeviceDetail(device);
    }
  },

  // 显示设备详情
  showDeviceDetail(device) {
    wx.showActionSheet({
      itemList: [`📍 ${device.name}`, `📞 导航到这里`],
      success: (res) => {
        if (res.tapIndex === 1) {
          wx.openLocation({
            latitude: device.latitude,
            longitude: device.longitude,
            name: device.name,
            address: device.address,
            scale: 18
          });
        }
      }
    });
  },

  // 计算距离显示
  formatDistance(distance) {
    if (distance < 1000) {
      return distance + 'm';
    } else {
      return (distance / 1000).toFixed(1) + 'km';
    }
  }
});

