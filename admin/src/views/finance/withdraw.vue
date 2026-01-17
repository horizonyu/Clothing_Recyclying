<template>
  <div class="withdraw-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button @click="$router.back()">返回</el-button>
          <span>提现审核</span>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="提现单号">
          <el-input v-model="searchForm.withdraw_id" placeholder="请输入提现单号" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
            <el-option label="待审核" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border>
        <el-table-column prop="withdraw_id" label="提现单号" width="180" />
        <el-table-column prop="user_id" label="用户ID" width="120" />
        <el-table-column prop="amount" label="金额(¥)" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="channel" label="渠道" width="100" />
        <el-table-column prop="created_at" label="申请时间" width="180" />
        <el-table-column prop="completed_at" label="完成时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'pending'" 
              link 
              type="success" 
              @click="handleAudit(row, 'approve')">
              通过
            </el-button>
            <el-button 
              v-if="row.status === 'pending'" 
              link 
              type="danger" 
              @click="handleAudit(row, 'reject')">
              拒绝
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getWithdrawList, auditWithdraw } from '@/api/admin'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({
  withdraw_id: '',
  status: ''
})
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getStatusType = (status) => {
  const typeMap = {
    'pending': 'warning',
    'processing': 'info',
    'success': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'pending': '待审核',
    'processing': '处理中',
    'success': '成功',
    'failed': '失败'
  }
  return textMap[status] || status
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    const { data } = await getWithdrawList(params)
    tableData.value = data.items || []
    pagination.total = data.total || 0
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    withdraw_id: '',
    status: ''
  })
  handleSearch()
}

const handleAudit = async (row, action) => {
  const actionText = action === 'approve' ? '通过' : '拒绝'
  await ElMessageBox.confirm(`确定要${actionText}该提现申请吗？`, '提示', {
    type: 'warning'
  })
  try {
    await auditWithdraw(row.withdraw_id, { action })
    ElMessage.success(`${actionText}成功`)
    loadData()
  } catch (error) {
    ElMessage.error(`${actionText}失败`)
  }
}

const handleSizeChange = () => {
  loadData()
}

const handlePageChange = () => {
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.withdraw-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-form {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
