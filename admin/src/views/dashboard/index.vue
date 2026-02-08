<template>
  <div class="dashboard">
    <!-- 数据概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="item in statsList" :key="item.key">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-trend" :class="item.trend > 0 ? 'up' : 'down'" v-if="item.trend !== 0">
              <el-icon><ArrowUp v-if="item.trend > 0" /><ArrowDown v-else /></el-icon>
              {{ Math.abs(item.trend) }}%
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备状态概览 -->
    <el-row :gutter="20" class="device-overview-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="section-header">
              <span>📡 设备状态概览</span>
              <el-button link type="primary" @click="$router.push('/device')">查看全部 →</el-button>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :xs="8" :sm="4" :md="3" v-for="item in deviceOverview" :key="item.key">
              <div class="device-stat-item" :class="item.colorClass">
                <div class="device-stat-icon">{{ item.icon }}</div>
                <div class="device-stat-value">{{ item.value }}</div>
                <div class="device-stat-label">{{ item.label }}</div>
              </div>
            </el-col>
          </el-row>
          <!-- 在线率进度条 -->
          <div class="online-rate-bar" v-if="onlineRate >= 0">
            <span class="rate-label">设备在线率</span>
            <el-progress
              :percentage="onlineRate"
              :color="onlineRate >= 80 ? '#67C23A' : onlineRate >= 50 ? '#E6A23C' : '#F56C6C'"
              :stroke-width="20"
              :text-inside="true"
              style="flex: 1"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :sm="24" :md="16">
        <el-card>
          <template #header>
            <span>近7日投递趋势</span>
          </template>
          <div ref="chartRef" style="width: 100%; height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <el-card>
          <template #header>
            <span>告警信息</span>
          </template>
          <el-scrollbar height="300px">
            <div v-if="alerts.length === 0" class="empty-alerts">暂无告警信息</div>
            <div v-else class="alert-list">
              <div v-for="alert in alerts" :key="alert.id" class="alert-item">
                <el-tag :type="getAlertType(alert.level)" size="small">{{ alert.level }}</el-tag>
                <span class="alert-text">{{ alert.message }}</span>
                <span class="alert-time">{{ alert.time }}</span>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { getDashboardStats, getDeviceStats } from '@/api/admin'

const chartRef = ref(null)
let chartInstance = null

const statsList = ref([
  { key: 'orders', label: '投递次数', value: '0', trend: 0 },
  { key: 'weight', label: '回收重量(kg)', value: '0', trend: 0 },
  { key: 'amount', label: '发放金额(¥)', value: '0.00', trend: 0 },
  { key: 'users', label: '活跃用户', value: '0', trend: 0 }
])

const alerts = ref([])
const onlineRate = ref(0)

const deviceOverview = ref([
  { key: 'total', label: '总设备', value: 0, icon: '📡', colorClass: 'blue' },
  { key: 'online', label: '在线', value: 0, icon: '🟢', colorClass: 'green' },
  { key: 'offline', label: '离线', value: 0, icon: '⚫', colorClass: 'gray' },
  { key: 'smoke_alert', label: '烟感告警', value: 0, icon: '🔥', colorClass: 'red' },
  { key: 'full_count', label: '仓体满载', value: 0, icon: '📦', colorClass: 'orange' },
  { key: 'using_count', label: '使用中', value: 0, icon: '👤', colorClass: 'blue' },
  { key: 'low_battery', label: '低电量', value: 0, icon: '🪫', colorClass: 'yellow' },
])

const getAlertType = (level) => {
  const typeMap = { '紧急': 'danger', '警告': 'warning', '提示': 'info' }
  return typeMap[level] || 'info'
}

const loadStats = async () => {
  try {
    const { data } = await getDashboardStats({ period: 'today' })
    statsList.value = [
      { key: 'orders', label: '投递次数', value: data.today_orders || '0', trend: data.orders_trend || 0 },
      { key: 'weight', label: '回收重量(kg)', value: data.today_weight || '0', trend: data.weight_trend || 0 },
      { key: 'amount', label: '发放金额(¥)', value: data.today_amount || '0.00', trend: data.amount_trend || 0 },
      { key: 'users', label: '活跃用户', value: data.active_users || '0', trend: data.users_trend || 0 }
    ]
    alerts.value = data.alerts || []
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadDeviceStats = async () => {
  try {
    const { data } = await getDeviceStats()
    onlineRate.value = data.online_rate || 0
    deviceOverview.value = [
      { key: 'total', label: '总设备', value: data.total || 0, icon: '📡', colorClass: 'blue' },
      { key: 'online', label: '在线', value: data.online || 0, icon: '🟢', colorClass: 'green' },
      { key: 'offline', label: '离线', value: data.offline || 0, icon: '⚫', colorClass: 'gray' },
      { key: 'smoke_alert', label: '烟感告警', value: data.smoke_alert || 0, icon: '🔥', colorClass: 'red' },
      { key: 'full_count', label: '仓体满载', value: data.full_count || 0, icon: '📦', colorClass: 'orange' },
      { key: 'using_count', label: '使用中', value: data.using_count || 0, icon: '👤', colorClass: 'blue' },
      { key: 'low_battery', label: '低电量', value: data.low_battery || 0, icon: '🪫', colorClass: 'yellow' },
    ]
  } catch (error) {
    console.error('加载设备统计失败:', error)
  }
}

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      name: '投递次数',
      type: 'line',
      data: [],
      smooth: true,
      areaStyle: { color: 'rgba(64, 158, 255, 0.15)' },
      itemStyle: { color: '#409eff' }
    }]
  }
  
  chartInstance.setOption(option)
  loadChartData()
}

const loadChartData = async () => {
  try {
    const { data } = await getDashboardStats({ period: '7days' })
    const dates = data.chart_data?.dates || []
    const values = data.chart_data?.values || []
    
    chartInstance.setOption({
      xAxis: { data: dates },
      series: [{ data: values }]
    })
  } catch (error) {
    console.error('加载图表数据失败:', error)
  }
}

let timer = null

onMounted(() => {
  loadStats()
  loadDeviceStats()
  setTimeout(() => { initChart() }, 100)
  
  timer = setInterval(() => {
    loadStats()
    loadDeviceStats()
  }, 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (chartInstance) chartInstance.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stats-row {
    margin-bottom: 20px;
  }

  .stat-card {
    .stat-content {
      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 8px;
      }

      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-bottom: 8px;
      }

      .stat-trend {
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 4px;

        &.up { color: #67c23a; }
        &.down { color: #f56c6c; }
      }
    }
  }

  .device-overview-row {
    margin-bottom: 20px;
  }

  .device-stat-item {
    text-align: center;
    padding: 16px 8px;
    border-radius: 8px;
    transition: background 0.2s;

    &:hover { background: #f5f7fa; }

    .device-stat-icon {
      font-size: 28px;
      margin-bottom: 6px;
    }

    .device-stat-value {
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 4px;
    }

    .device-stat-label {
      font-size: 12px;
      color: #909399;
    }

    &.green .device-stat-value { color: #67C23A; }
    &.red .device-stat-value { color: #F56C6C; }
    &.orange .device-stat-value { color: #E6A23C; }
    &.gray .device-stat-value { color: #909399; }
    &.blue .device-stat-value { color: #409EFF; }
    &.yellow .device-stat-value { color: #f0a020; }
  }

  .online-rate-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #ebeef5;

    .rate-label {
      font-size: 14px;
      color: #606266;
      white-space: nowrap;
    }
  }

  .charts-row {
    margin-top: 20px;
  }

  .alert-list {
    .alert-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 0;
      border-bottom: 1px solid #ebeef5;

      &:last-child { border-bottom: none; }

      .alert-text {
        flex: 1;
        font-size: 14px;
      }

      .alert-time {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .empty-alerts {
    text-align: center;
    color: #909399;
    padding: 50px 0;
  }
}
</style>
