<template>
  <div class="user-detail-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-button @click="$router.back()">返回</el-button>
          <span>用户详情</span>
        </div>
      </template>

      <div v-if="userInfo" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">{{ userInfo.user_id }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ userInfo.nickname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ userInfo.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="userInfo.status === 1 ? 'success' : 'danger'">
              {{ userInfo.status === 1 ? '正常' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="余额(¥)">{{ userInfo.balance || 0 }}</el-descriptions-item>
          <el-descriptions-item label="积分">{{ userInfo.points || 0 }}</el-descriptions-item>
          <el-descriptions-item label="累计重量(kg)">{{ userInfo.total_weight || 0 }}</el-descriptions-item>
          <el-descriptions-item label="投递次数">{{ userInfo.total_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="实名认证">
            <el-tag :type="userInfo.is_verified ? 'success' : 'info'">
              {{ userInfo.is_verified ? '已认证' : '未认证' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ userInfo.created_at }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getUserDetail } from '@/api/admin'

const route = useRoute()
const loading = ref(false)
const userInfo = ref(null)

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await getUserDetail(route.params.id)
    userInfo.value = data
  } catch (error) {
    ElMessage.error('加载用户详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.user-detail-page {
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
