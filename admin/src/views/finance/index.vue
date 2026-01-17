<template>
  <div class="finance-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>财务管理</span>
          <el-button type="primary" @click="$router.push('/finance/withdraw')">提现审核</el-button>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">¥{{ stats.total_income || '0.00' }}</div>
              <div class="stat-label">累计收入</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">¥{{ stats.total_withdraw || '0.00' }}</div>
              <div class="stat-label">累计提现</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">¥{{ stats.pending_withdraw || '0.00' }}</div>
              <div class="stat-label">待审核提现</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">¥{{ stats.balance || '0.00' }}</div>
              <div class="stat-label">平台余额</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const stats = ref({
  total_income: '0.00',
  total_withdraw: '0.00',
  pending_withdraw: '0.00',
  balance: '0.00'
})

const loadStats = async () => {
  try {
    // TODO: 调用API获取统计数据
    stats.value = {
      total_income: '12580.50',
      total_withdraw: '8560.30',
      pending_withdraw: '320.00',
      balance: '3700.20'
    }
  } catch (error) {
    ElMessage.error('加载统计数据失败')
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style lang="scss" scoped>
.finance-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stats-row {
    margin-top: 20px;
  }

  .stat-card {
    .stat-content {
      text-align: center;

      .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 8px;
      }

      .stat-label {
        font-size: 14px;
        color: #909399;
      }
    }
  }
}
</style>
