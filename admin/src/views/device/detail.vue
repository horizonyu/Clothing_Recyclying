<template>
  <div class="device-detail-page" v-loading="loading">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回设备列表
      </el-button>
      <el-button type="primary" @click="loadData">
        <el-icon><Refresh /></el-icon> 刷新数据
      </el-button>
    </div>

    <template v-if="device">
      <!-- 设备基本信息 -->
      <el-row :gutter="16">
        <el-col :span="24">
          <el-card>
            <template #header>
              <div class="section-header">
                <span>📡 设备基本信息</span>
                <el-tag :type="getStatusType(device.status)" effect="dark" size="large">
                  {{ getStatusText(device.status) }}
                </el-tag>
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
        <!-- 电池电量 -->
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

        <!-- 烟感状态 -->
        <el-col :xs="12" :sm="8" :md="4">
          <el-card class="status-card" shadow="hover"
            :class="{ 'alarm-card': device.smoke_sensor_status === 1 }">
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

        <!-- 仓体状态 -->
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

        <!-- 投放窗口 -->
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

        <!-- 使用状态 -->
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

        <!-- 容量 -->
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
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import { getDeviceDetail } from '@/api/admin'
import * as echarts from 'echarts'

const route = useRoute()
const loading = ref(false)
const device = ref(null)
const chartRef = ref(null)
let chartInstance = null

const getStatusType = (status) => {
  const m = { 'online': 'success', 'offline': 'info', 'maintenance': 'warning', 'error': 'danger' }
  return m[status] || 'info'
}

const getStatusText = (status) => {
  const m = { 'online': '在线', 'offline': '离线', 'maintenance': '维护中', 'error': '故障' }
  return m[status] || status
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
    :deep(.el-card__body) {
      padding: 16px;
    }

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
      .status-value {
        font-size: 18px;
        font-weight: 700;
        line-height: 1.3;
      }
      .status-label {
        font-size: 12px;
        color: #909399;
        margin-top: 2px;
      }
    }
  }
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(245, 108, 108, 0); }
}
</style>
