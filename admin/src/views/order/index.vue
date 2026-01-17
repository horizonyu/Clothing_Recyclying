<template>
  <div class="order-page">
    <el-card>
      <template #header>
        <span>订单列表</span>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="订单号">
          <el-input v-model="searchForm.order_id" placeholder="请输入订单号" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
            <el-option label="待领取" value="pending" />
            <el-option label="已领取" value="claimed" />
            <el-option label="已过期" value="expired" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border>
        <el-table-column prop="order_id" label="订单号" width="180" />
        <el-table-column prop="user_id" label="用户ID" width="120" />
        <el-table-column prop="device_id" label="设备ID" width="120" />
        <el-table-column prop="weight" label="重量(kg)" width="100" />
        <el-table-column prop="amount" label="金额(¥)" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'pending'" link type="success" @click="handleAudit(row)">审核</el-button>
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getOrderList } from '@/api/admin'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({
  order_id: '',
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
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    const { data } = await getOrderList(params)
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
    order_id: '',
    status: ''
  })
  handleSearch()
}

const handleDetail = (row) => {
  router.push(`/order/detail/${row.order_id}`)
}

const handleAudit = async (row) => {
  // TODO: 审核订单
  ElMessage.info('审核功能待实现')
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
.order-page {
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
