<template>
  <div class="device-detail-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-button @click="$router.back()">返回</el-button>
          <span>设备详情</span>
        </div>
      </template>

      <div v-if="deviceInfo" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="设备ID">{{ deviceInfo.device_id }}</el-descriptions-item>
          <el-descriptions-item label="设备名称">{{ deviceInfo.name }}</el-descriptions-item>
          <el-descriptions-item label="地址">{{ deviceInfo.address }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(deviceInfo.status)">{{ getStatusText(deviceInfo.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="单价(元/kg)">{{ deviceInfo.unit_price }}</el-descriptions-item>
          <el-descriptions-item label="累计订单">{{ deviceInfo.total_orders || 0 }}</el-descriptions-item>
          <el-descriptions-item label="累计重量(kg)">{{ deviceInfo.total_weight || 0 }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ deviceInfo.created_at }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDeviceDetail } from '@/api/admin'

const route = useRoute()
const loading = ref(false)
const deviceInfo = ref(null)

const getStatusType = (status) => {
  const typeMap = {
    'online': 'success',
    'offline': 'info',
    'error': 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'online': '在线',
    'offline': '离线',
    'error': '故障'
  }
  return textMap[status] || status
}

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await getDeviceDetail(route.params.id)
    deviceInfo.value = data
  } catch (error) {
    ElMessage.error('加载设备详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.device-detail-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-content {
    margin-top: 20px;
  }
}
</style>
