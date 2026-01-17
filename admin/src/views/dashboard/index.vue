<template>
  <div class="dashboard">
    <!-- 数据概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="item in statsList" :key="item.key">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-trend" :class="item.trend > 0 ? 'up' : 'down'">
              <el-icon><ArrowUp v-if="item.trend > 0" /><ArrowDown v-else /></el-icon>
              {{ Math.abs(item.trend) }}%
            </div>
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
import { getDashboardStats } from '@/api/admin'

const chartRef = ref(null)
let chartInstance = null

const statsList = ref([
  { key: 'orders', label: '投递次数', value: '0', trend: 0 },
  { key: 'weight', label: '回收重量(kg)', value: '0', trend: 0 },
  { key: 'amount', label: '发放金额(¥)', value: '0.00', trend: 0 },
  { key: 'users', label: '活跃用户', value: '0', trend: 0 }
])

const alerts = ref([])

const getAlertType = (level) => {
  const typeMap = {
    '紧急': 'danger',
    '警告': 'warning',
    '提示': 'info'
  }
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

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '投递次数',
        type: 'line',
        data: [],
        smooth: true,
        itemStyle: { color: '#409eff' }
      }
    ]
  }
  
  chartInstance.setOption(option)
  
  // 加载数据
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

onMounted(() => {
  loadStats()
  setTimeout(() => {
    initChart()
  }, 100)
  
  // 定时刷新
  const timer = setInterval(() => {
    loadStats()
  }, 60000) // 每分钟刷新一次
  
  onUnmounted(() => {
    clearInterval(timer)
    if (chartInstance) {
      chartInstance.dispose()
    }
  })
})
</script>

<style lang="scss" scoped>
.dashboard {
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

        &.up {
          color: #67c23a;
        }

        &.down {
          color: #f56c6c;
        }
      }
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

      &:last-child {
        border-bottom: none;
      }

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
