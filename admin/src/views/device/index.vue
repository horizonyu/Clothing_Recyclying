<template>
  <div class="device-page">
    <!-- 设备状态概览 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="8" :md="4" v-for="item in deviceStats" :key="item.key">
        <el-card class="stat-card" :class="item.colorClass" shadow="hover">
          <div class="stat-icon">
            <el-icon :size="24"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备列表</span>
          <el-button type="primary" @click="loadData">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="设备ID">
          <el-input v-model="searchForm.device_id" placeholder="请输入设备ID" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="维护中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="device_id" label="设备ID" width="160" fixed />
        <el-table-column prop="name" label="设备名称" min-width="120" />
        <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
        <el-table-column label="运行状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="dark" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="连接" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.connection_type === 'websocket'" type="success" size="small">WS</el-tag>
            <el-tag v-else-if="row.connection_type === 'long_polling'" size="small">LP</el-tag>
            <el-tag v-else type="info" size="small">离线</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="电量" width="100" align="center">
          <template #default="{ row }">
            <div class="battery-cell" v-if="row.battery_level != null">
              <el-icon :color="getBatteryColor(row.battery_level)">
                <component :is="getBatteryIcon(row.battery_level)" />
              </el-icon>
              <span :style="{ color: getBatteryColor(row.battery_level) }">{{ row.battery_level }}%</span>
            </div>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column label="烟感" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.smoke_sensor_status === 1" type="danger" size="small" effect="dark">告警</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="仓体" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.recycle_bin_full === 1" type="warning" size="small" effect="dark">已满</el-tag>
            <el-tag v-else type="success" size="small">未满</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="使用" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_using === 1" type="primary" size="small" effect="dark">使用中</el-tag>
            <el-tag v-else size="small">空闲</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_orders" label="累计订单" width="90" align="center" />
        <el-table-column label="累计重量" width="100" align="center">
          <template #default="{ row }">
            {{ row.total_weight }} kg
          </template>
        </el-table-column>
        <el-table-column label="最后心跳" width="160" align="center">
          <template #default="{ row }">
            <span v-if="row.last_heartbeat">{{ row.last_heartbeat }}</span>
            <span v-else class="text-muted">从未上报</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="warning" @click="handleQueryStatus(row)">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button link type="primary" @click="handleDetail(row)">
              <el-icon><View /></el-icon> 详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, View, Search } from '@element-plus/icons-vue'
import { getDeviceList, getDeviceStats, queryDeviceStatus } from '@/api/admin'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({
  device_id: '',
  status: ''
})
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 设备状态统计
const deviceStats = ref([
  { key: 'total', label: '总设备', value: 0, icon: 'Monitor', colorClass: 'stat-blue' },
  { key: 'online', label: '在线', value: 0, icon: 'CircleCheck', colorClass: 'stat-green' },
  { key: 'offline', label: '离线', value: 0, icon: 'CircleClose', colorClass: 'stat-gray' },
  { key: 'smoke_alert', label: '烟感告警', value: 0, icon: 'WarningFilled', colorClass: 'stat-red' },
  { key: 'full_count', label: '仓体满载', value: 0, icon: 'Box', colorClass: 'stat-orange' },
  { key: 'low_battery', label: '低电量', value: 0, icon: 'Lightning', colorClass: 'stat-yellow' },
])

const getStatusType = (status) => {
  const typeMap = { 'online': 'success', 'offline': 'info', 'maintenance': 'warning', 'error': 'danger' }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = { 'online': '在线', 'offline': '离线', 'maintenance': '维护中', 'error': '故障' }
  return textMap[status] || status
}

const getBatteryColor = (level) => {
  if (level == null) return '#909399'
  if (level <= 10) return '#F56C6C'
  if (level <= 20) return '#E6A23C'
  return '#67C23A'
}

const getBatteryIcon = (level) => {
  if (level == null) return 'Minus'
  if (level <= 20) return 'WarningFilled'
  return 'CircleCheckFilled'
}

const loadStats = async () => {
  try {
    const { data } = await getDeviceStats()
    deviceStats.value = [
      { key: 'total', label: '总设备', value: data.total || 0, icon: 'Monitor', colorClass: 'stat-blue' },
      { key: 'online', label: '在线', value: data.online || 0, icon: 'CircleCheck', colorClass: 'stat-green' },
      { key: 'offline', label: '离线', value: data.offline || 0, icon: 'CircleClose', colorClass: 'stat-gray' },
      { key: 'smoke_alert', label: '烟感告警', value: data.smoke_alert || 0, icon: 'WarningFilled', colorClass: 'stat-red' },
      { key: 'full_count', label: '仓体满载', value: data.full_count || 0, icon: 'Box', colorClass: 'stat-orange' },
      { key: 'low_battery', label: '低电量', value: data.low_battery || 0, icon: 'Lightning', colorClass: 'stat-yellow' },
    ]
  } catch (error) {
    console.error('加载设备统计失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (searchForm.device_id) params.device_id = searchForm.device_id
    if (searchForm.status) params.status = searchForm.status

    const { data } = await getDeviceList(params)
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch (error) {
    ElMessage.error('加载设备列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, { device_id: '', status: '' })
  handleSearch()
}

const handleQueryStatus = async (row) => {
  try {
    const { data } = await queryDeviceStatus(row.device_id)
    const method = data?.delivery_method
    
    if (method === 'websocket' || method === 'long_polling') {
      const via = method === 'websocket' ? 'WebSocket' : '长轮询'
      ElMessage.success({
        message: `查询命令已通过 ${via} 实时下发到 ${row.device_id}，正在等待响应...`,
        duration: 3000,
      })
      setTimeout(() => { loadStats(); loadData() }, 3000)
    } else {
      ElMessage.warning({
        message: `${row.device_id} 当前不在线，命令已排队，设备上线后将自动响应`,
        duration: 5000,
      })
      setTimeout(() => { loadStats(); loadData() }, 10000)
    }
  } catch (error) {
    ElMessage.error('下发查询指令失败')
  }
}

const handleDetail = (row) => {
  router.push(`/device/detail/${row.device_id}`)
}

const handleSizeChange = () => { loadData() }
const handlePageChange = () => { loadData() }

let refreshTimer = null

onMounted(() => {
  loadStats()
  loadData()
  // 每30秒自动刷新
  refreshTimer = setInterval(() => {
    loadStats()
    loadData()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style lang="scss" scoped>
.device-page {
  .stats-row {
    margin-bottom: 16px;
  }

  .stat-card {
    display: flex;
    align-items: center;
    padding: 0;
    cursor: default;

    :deep(.el-card__body) {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      width: 100%;
    }

    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      flex-shrink: 0;
    }

    .stat-info {
      .stat-value {
        font-size: 22px;
        font-weight: 700;
        line-height: 1.2;
      }
      .stat-label {
        font-size: 13px;
        color: #909399;
        margin-top: 2px;
      }
    }

    &.stat-blue .stat-icon { background: #409eff; }
    &.stat-green .stat-icon { background: #67c23a; }
    &.stat-gray .stat-icon { background: #909399; }
    &.stat-red .stat-icon { background: #f56c6c; }
    &.stat-orange .stat-icon { background: #e6a23c; }
    &.stat-yellow .stat-icon { background: #f0a020; }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-form {
    margin-bottom: 16px;
  }

  .battery-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    font-size: 13px;
    font-weight: 500;
  }

  .text-muted {
    color: #c0c4cc;
  }

  .pagination {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
