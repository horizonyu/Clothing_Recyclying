<template>
  <div class="order-detail-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-button @click="$router.back()">返回</el-button>
          <span>订单详情</span>
        </div>
      </template>

      <div v-if="orderInfo" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ orderInfo.order_id }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ orderInfo.user_id }}</el-descriptions-item>
          <el-descriptions-item label="设备ID">{{ orderInfo.device_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(orderInfo.status)">{{ getStatusText(orderInfo.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="重量(kg)">{{ orderInfo.weight }}</el-descriptions-item>
          <el-descriptions-item label="金额(¥)">{{ orderInfo.amount }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ orderInfo.created_at }}</el-descriptions-item>
          <el-descriptions-item label="领取时间">{{ orderInfo.claimed_at || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getOrderDetail } from '@/api/admin'

const route = useRoute()
const loading = ref(false)
const orderInfo = ref(null)

const getStatusType = (status) => {
  const typeMap = {
    'pending': 'warning',
    'claimed': 'success',
    'expired': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'pending': '待领取',
    'claimed': '已领取',
    'expired': '已过期'
  }
  return textMap[status] || status
}

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await getOrderDetail(route.params.id)
    orderInfo.value = data
  } catch (error) {
    ElMessage.error('加载订单详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.order-detail-page {
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
