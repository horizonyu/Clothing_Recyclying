<template>
  <div class="device-detail-page" v-loading="loading">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回设备列表
      </el-button>
      <div style="display: flex; gap: 8px;">
        <el-button type="warning" @click="handleQueryStatus" :loading="queryLoading">
          <el-icon><Search /></el-icon> 主动查询设备状态
        </el-button>
        <el-button type="primary" @click="loadData">
          <el-icon><Refresh /></el-icon> 刷新数据
        </el-button>
      </div>
    </div>

    <template v-if="device">
      <!-- 设备基本信息 -->
      <el-row :gutter="16">
        <el-col :span="24">
          <el-card>
            <template #header>
              <div class="section-header">
                <span>📡 设备基本信息</span>
                <div style="display: flex; gap: 8px; align-items: center;">
                  <el-tag :type="getConnTypeColor(device.connection_type)" effect="plain" size="small">
                    {{ getConnTypeText(device.connection_type) }}
                  </el-tag>
                  <el-tag :type="getStatusType(device.status)" effect="dark" size="large">
                    {{ getStatusText(device.status) }}
                  </el-tag>
                </div>
              </div>
            </template>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="设备ID">
                <el-text type="primary" tag="b">{{ device.device_id }}</el-text>
              </el-descriptions-item>
              <el-descriptions-item label="设备名称">{{ device.name }}</el-descriptions-item>
              <el-descriptions-item label="固件版本">{{ device.firmware_version || '未知' }}</el-descriptions-item>
              <el-descriptions-item label="设备地址" :span="2">{{ device.address || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="回收单价">¥{{ device.unit_price }} /kg</el-descriptions-item>
              <el-descriptions-item label="经度">{{ device.longitude || '--' }}</el-descriptions-item>
              <el-descriptions-item label="纬度">{{ device.latitude || '--' }}</el-descriptions-item>
              <el-descriptions-item label="最后心跳">
                <span v-if="device.last_heartbeat">{{ device.last_heartbeat }}</span>
                <el-text v-else type="info">从未上报</el-text>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <!-- 实时状态卡片 -->
      <el-row :gutter="16" class="status-cards">
        <el-col :xs="12" :sm="8" :md="4">
          <el-card class="status-card" shadow="hover">
            <div class="status-card-inner">
              <div class="status-icon" :style="{ background: getBatteryBg(device.battery_level) }">🔋</div>
              <div class="status-info">
                <div class="status-value" :style="{ color: getBatteryColor(device.battery_level) }">
                  {{ device.battery_level != null ? device.battery_level + '%' : '--' }}
                </div>
                <div class="status-label">电池电量</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="8" :md="4">
          <el-card class="status-card" shadow="hover" :class="{ 'alarm-card': device.smoke_sensor_status === 1 }">
            <div class="status-card-inner">
              <div class="status-icon" :style="{ background: device.smoke_sensor_status === 1 ? '#fef0f0' : '#f0f9eb' }">
                {{ device.smoke_sensor_status === 1 ? '🔥' : '✅' }}
              </div>
              <div class="status-info">
                <div class="status-value" :style="{ color: device.smoke_sensor_status === 1 ? '#F56C6C' : '#67C23A' }">
                  {{ device.smoke_sensor_status === 1 ? '告警' : '正常' }}
                </div>
                <div class="status-label">烟感状态</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="8" :md="4">
          <el-card class="status-card" shadow="hover">
            <div class="status-card-inner">
              <div class="status-icon" :style="{ background: device.recycle_bin_full === 1 ? '#fdf6ec' : '#f0f9eb' }">
                {{ device.recycle_bin_full === 1 ? '📦' : '📭' }}
              </div>
              <div class="status-info">
                <div class="status-value" :style="{ color: device.recycle_bin_full === 1 ? '#E6A23C' : '#67C23A' }">
                  {{ device.recycle_bin_full === 1 ? '已满' : '未满' }}
                </div>
                <div class="status-label">仓体状态</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="8" :md="4">
          <el-card class="status-card" shadow="hover">
            <div class="status-card-inner">
              <div class="status-icon" :style="{ background: device.delivery_window_open === 1 ? '#ecf5ff' : '#f4f4f5' }">
                {{ device.delivery_window_open === 1 ? '🚪' : '🔒' }}
              </div>
              <div class="status-info">
                <div class="status-value" :style="{ color: device.delivery_window_open === 1 ? '#409EFF' : '#909399' }">
                  {{ device.delivery_window_open === 1 ? '已打开' : '已关闭' }}
                </div>
                <div class="status-label">投放窗口</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="8" :md="4">
          <el-card class="status-card" shadow="hover">
            <div class="status-card-inner">
              <div class="status-icon" :style="{ background: device.is_using === 1 ? '#ecf5ff' : '#f4f4f5' }">
                {{ device.is_using === 1 ? '👤' : '💤' }}
              </div>
              <div class="status-info">
                <div class="status-value" :style="{ color: device.is_using === 1 ? '#409EFF' : '#909399' }">
                  {{ device.is_using === 1 ? '使用中' : '空闲' }}
                </div>
                <div class="status-label">使用状态</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="8" :md="4">
          <el-card class="status-card" shadow="hover">
            <div class="status-card-inner">
              <div class="status-icon" style="background: #f0f9eb">📊</div>
              <div class="status-info">
                <div class="status-value">{{ device.capacity_percent || 0 }}%</div>
                <div class="status-label">容量占比</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 📷 摄像头实时画面 -->
      <el-row :gutter="16">
        <el-col :span="24">
          <el-card>
            <template #header>
              <div class="section-header">
                <span>📷 摄像头画面（最近一次上报）</span>
                <el-button link type="primary" @click="showCameraHistory = true" v-if="device.camera_total_count > 0">
                  查看历史记录 ({{ device.camera_total_count }}张) →
                </el-button>
              </div>
            </template>

            <div v-if="hasCameraImages" class="camera-section">
              <!-- 摄像头1: 回收箱内部 -->
              <div class="camera-group">
                <div class="camera-title">
                  <el-tag type="primary" size="small">摄像头1</el-tag>
                  <span>回收箱内部</span>
                </div>
                <div class="camera-images" v-if="device.camera_images.camera_1.length > 0">
                  <div
                    class="camera-image-item"
                    v-for="(img, idx) in device.camera_images.camera_1"
                    :key="'c1-' + idx"
                    @click="previewImage(img.image_data)"
                  >
                    <el-image
                      :src="getImageSrc(img.image_data)"
                      fit="cover"
                      :preview-src-list="getCameraPreviewList(1)"
                      :initial-index="idx"
                      :preview-teleported="true"
                    />
                    <div class="image-time">{{ img.captured_at }}</div>
                  </div>
                </div>
                <div v-else class="no-images">暂无图片</div>
              </div>

              <!-- 摄像头2: 用户 -->
              <div class="camera-group">
                <div class="camera-title">
                  <el-tag type="success" size="small">摄像头2</el-tag>
                  <span>用户画面</span>
                </div>
                <div class="camera-images" v-if="device.camera_images.camera_2.length > 0">
                  <div
                    class="camera-image-item"
                    v-for="(img, idx) in device.camera_images.camera_2"
                    :key="'c2-' + idx"
                    @click="previewImage(img.image_data)"
                  >
                    <el-image
                      :src="getImageSrc(img.image_data)"
                      fit="cover"
                      :preview-src-list="getCameraPreviewList(2)"
                      :initial-index="idx"
                      :preview-teleported="true"
                    />
                    <div class="image-time">{{ img.captured_at }}</div>
                  </div>
                </div>
                <div v-else class="no-images">暂无图片</div>
              </div>
            </div>

            <div v-else class="no-camera-data">
              <el-empty description="暂无摄像头数据" :image-size="80" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 业务统计 + 趋势图 -->
      <el-row :gutter="16">
        <el-col :xs="24" :md="8">
          <el-card>
            <template #header><span>📈 业务统计</span></template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="累计订单数">
                <el-text type="primary" tag="b">{{ device.total_orders }}</el-text> 单
              </el-descriptions-item>
              <el-descriptions-item label="累计回收重量">
                <el-text type="primary" tag="b">{{ device.total_weight }}</el-text> kg
              </el-descriptions-item>
              <el-descriptions-item label="累计发放金额">
                <el-text type="primary" tag="b">¥{{ device.total_amount }}</el-text>
              </el-descriptions-item>
              <el-descriptions-item label="今日订单数">
                <el-text type="success" tag="b">{{ device.today_orders }}</el-text> 单
              </el-descriptions-item>
              <el-descriptions-item label="今日回收重量">
                <el-text type="success" tag="b">{{ device.today_weight }}</el-text> kg
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="16">
          <el-card>
            <template #header><span>📊 近7日投递趋势</span></template>
            <div ref="chartRef" style="width: 100%; height: 280px"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 时间信息 -->
      <el-row :gutter="16">
        <el-col :span="24">
          <el-card>
            <template #header><span>⏰ 时间信息</span></template>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="创建时间">{{ device.created_at }}</el-descriptions-item>
              <el-descriptions-item label="最后更新">{{ device.updated_at }}</el-descriptions-item>
              <el-descriptions-item label="最后心跳">{{ device.last_heartbeat || '从未上报' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 摄像头历史记录弹窗 -->
    <el-dialog
      v-model="showCameraHistory"
      title="📷 摄像头图片历史记录"
      width="900px"
      :destroy-on-close="true"
    >
      <div v-loading="historyLoading">
        <div v-if="cameraHistory.length === 0" class="no-camera-data">
          <el-empty description="暂无历史图片" :image-size="60" />
        </div>
        <div v-else>
          <div v-for="batch in cameraHistory" :key="batch.batch_id" class="history-batch">
            <div class="batch-header">
              <el-tag size="small">{{ batch.captured_at }}</el-tag>
              <span class="batch-id">批次: {{ batch.batch_id }}</span>
            </div>
            <el-row :gutter="12">
              <!-- 摄像头1 -->
              <el-col :span="12" v-if="batch.camera_1.length > 0">
                <div class="history-camera-title">
                  <el-tag type="primary" size="small">摄像头1 - 回收箱内部</el-tag>
                </div>
                <div class="history-images">
                  <el-image
                    v-for="(img, idx) in batch.camera_1"
                    :key="'h-c1-' + img.id"
                    :src="getImageSrc(img.image_data)"
                    fit="cover"
                    class="history-image"
                    :preview-src-list="batch.camera_1.map(i => getImageSrc(i.image_data))"
                    :initial-index="idx"
                    :preview-teleported="true"
                  />
                </div>
              </el-col>
              <!-- 摄像头2 -->
              <el-col :span="12" v-if="batch.camera_2.length > 0">
                <div class="history-camera-title">
                  <el-tag type="success" size="small">摄像头2 - 用户画面</el-tag>
                </div>
                <div class="history-images">
                  <el-image
                    v-for="(img, idx) in batch.camera_2"
                    :key="'h-c2-' + img.id"
                    :src="getImageSrc(img.image_data)"
                    fit="cover"
                    class="history-image"
                    :preview-src-list="batch.camera_2.map(i => getImageSrc(i.image_data))"
                    :initial-index="idx"
                    :preview-teleported="true"
                  />
                </div>
              </el-col>
            </el-row>
          </div>
          <!-- 分页 -->
          <div class="history-pagination">
            <el-pagination
              v-model:current-page="historyPage"
              :page-size="5"
              :total="historyTotal"
              layout="prev, pager, next"
              @current-change="loadCameraHistory"
            />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Refresh, Search } from '@element-plus/icons-vue'
import { getDeviceDetail, getDeviceCameraImages, queryDeviceStatus } from '@/api/admin'
import * as echarts from 'echarts'

const route = useRoute()
const loading = ref(false)
const queryLoading = ref(false)
const device = ref(null)
const chartRef = ref(null)
let chartInstance = null

// 摄像头历史
const showCameraHistory = ref(false)
const historyLoading = ref(false)
const cameraHistory = ref([])
const historyPage = ref(1)
const historyTotal = ref(0)

const hasCameraImages = computed(() => {
  if (!device.value || !device.value.camera_images) return false
  const cam = device.value.camera_images
  return (cam.camera_1 && cam.camera_1.length > 0) || (cam.camera_2 && cam.camera_2.length > 0)
})

const getStatusType = (status) => {
  const m = { 'online': 'success', 'offline': 'info', 'maintenance': 'warning', 'error': 'danger' }
  return m[status] || 'info'
}

const getStatusText = (status) => {
  const m = { 'online': '在线', 'offline': '离线', 'maintenance': '维护中', 'error': '故障' }
  return m[status] || status
}

const getConnTypeColor = (type) => {
  const m = { 'websocket': 'success', 'long_polling': '', 'offline': 'info' }
  return m[type] || 'info'
}

const getConnTypeText = (type) => {
  const m = { 'websocket': '🔗 WebSocket 长连接', 'long_polling': '⏳ 长轮询', 'offline': '⚫ 无实时连接' }
  return m[type] || '⚫ 无实时连接'
}

const getBatteryColor = (level) => {
  if (level == null) return '#909399'
  if (level <= 10) return '#F56C6C'
  if (level <= 20) return '#E6A23C'
  return '#67C23A'
}

const getBatteryBg = (level) => {
  if (level == null) return '#f4f4f5'
  if (level <= 10) return '#fef0f0'
  if (level <= 20) return '#fdf6ec'
  return '#f0f9eb'
}

/**
 * 将Base64图片数据转换为可显示的src
 * 自动检测是否已有data:前缀
 */
const getImageSrc = (base64Data) => {
  if (!base64Data) return ''
  if (base64Data.startsWith('data:')) return base64Data
  // 尝试检测图片类型
  if (base64Data.startsWith('iVBOR')) return `data:image/png;base64,${base64Data}`
  if (base64Data.startsWith('/9j/')) return `data:image/jpeg;base64,${base64Data}`
  if (base64Data.startsWith('R0lGO')) return `data:image/gif;base64,${base64Data}`
  // 默认当作PNG
  return `data:image/png;base64,${base64Data}`
}

const getCameraPreviewList = (cameraType) => {
  if (!device.value || !device.value.camera_images) return []
  const key = `camera_${cameraType}`
  const images = device.value.camera_images[key] || []
  return images.map(img => getImageSrc(img.image_data))
}

const previewImage = (base64Data) => {
  // el-image组件自带preview功能，这里留空备用
}

const initChart = (dailyOrders) => {
  if (!chartRef.value) return
  if (chartInstance) chartInstance.dispose()

  chartInstance = echarts.init(chartRef.value)
  const dates = (dailyOrders || []).map(d => d.date)
  const values = (dailyOrders || []).map(d => d.count)

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      name: '投递次数',
      type: 'line',
      data: values,
      smooth: true,
      areaStyle: { color: 'rgba(64, 158, 255, 0.15)' },
      lineStyle: { color: '#409eff', width: 2 },
      itemStyle: { color: '#409eff' }
    }]
  })
}

/**
 * 主动查询设备状态
 * 命令下发优先级: WebSocket > 长轮询 > 数据库排队
 */
const handleQueryStatus = async () => {
  queryLoading.value = true
  try {
    const { data } = await queryDeviceStatus(route.params.id)
    const method = data?.delivery_method
    
    if (method === 'websocket') {
      ElMessage.success({
        message: '查询命令已通过 WebSocket 实时下发到设备，正在等待响应...',
        duration: 3000,
      })
      setTimeout(() => { loadData() }, 3000)
    } else if (method === 'long_polling') {
      ElMessage.success({
        message: '查询命令已通过长轮询实时下发到设备，正在等待响应...',
        duration: 3000,
      })
      setTimeout(() => { loadData() }, 3000)
    } else {
      ElMessage.warning({
        message: '设备当前不在线，命令已排队，设备上线后将自动响应',
        duration: 5000,
      })
      setTimeout(() => { loadData() }, 10000)
    }
  } catch (error) {
    ElMessage.error('下发查询指令失败')
  } finally {
    queryLoading.value = false
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await getDeviceDetail(route.params.id)
    device.value = data
    await nextTick()
    initChart(data.daily_orders)
  } catch (error) {
    ElMessage.error('加载设备详情失败')
  } finally {
    loading.value = false
  }
}

const loadCameraHistory = async (page) => {
  historyLoading.value = true
  if (page) historyPage.value = page
  try {
    const { data } = await getDeviceCameraImages(route.params.id, {
      page: historyPage.value,
      page_size: 5,
    })
    cameraHistory.value = data.items || []
    historyTotal.value = data.total || 0
  } catch (error) {
    ElMessage.error('加载摄像头历史失败')
  } finally {
    historyLoading.value = false
  }
}

// 打开历史弹窗时自动加载
watch(showCameraHistory, (val) => {
  if (val) {
    historyPage.value = 1
    loadCameraHistory()
  }
})

let refreshTimer = null

onMounted(() => {
  loadData()
  refreshTimer = setInterval(loadData, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (chartInstance) chartInstance.dispose()
})
</script>

<style lang="scss" scoped>
.device-detail-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .el-row {
    margin-bottom: 16px;
  }

  .status-cards {
    margin-bottom: 16px;
  }

  .status-card {
    :deep(.el-card__body) { padding: 16px; }

    &.alarm-card {
      border: 1px solid #F56C6C;
      animation: pulse 2s infinite;
    }

    .status-card-inner {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .status-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      flex-shrink: 0;
    }

    .status-info {
      .status-value { font-size: 18px; font-weight: 700; line-height: 1.3; }
      .status-label { font-size: 12px; color: #909399; margin-top: 2px; }
    }
  }

  // 摄像头区域
  .camera-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .camera-group {
    .camera-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      font-size: 14px;
      font-weight: 500;
      color: #303133;
    }

    .camera-images {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .camera-image-item {
      width: 200px;
      cursor: pointer;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #ebeef5;
      transition: all 0.3s;

      &:hover {
        border-color: #409eff;
        box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
        transform: translateY(-2px);
      }

      :deep(.el-image) {
        width: 200px;
        height: 150px;
        display: block;
      }

      .image-time {
        padding: 6px 8px;
        font-size: 11px;
        color: #909399;
        background: #fafafa;
        text-align: center;
      }
    }

    .no-images {
      color: #c0c4cc;
      font-size: 13px;
      padding: 20px;
      text-align: center;
      border: 1px dashed #dcdfe6;
      border-radius: 8px;
    }
  }

  .no-camera-data {
    padding: 20px 0;
  }
}

// 历史记录弹窗样式
.history-batch {
  padding: 16px 0;
  border-bottom: 1px solid #ebeef5;

  &:last-child { border-bottom: none; }

  .batch-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;

    .batch-id {
      font-size: 12px;
      color: #c0c4cc;
    }
  }

  .history-camera-title {
    margin-bottom: 8px;
  }

  .history-images {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .history-image {
    width: 140px;
    height: 105px;
    border-radius: 6px;
    border: 1px solid #ebeef5;
    cursor: pointer;

    &:hover {
      border-color: #409eff;
    }
  }
}

.history-pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(245, 108, 108, 0); }
}
</style>
