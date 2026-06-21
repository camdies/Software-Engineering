<template>
  <div class="page-card">
    <div class="page-header">
      <h1>操作日志</h1>
    </div>

    <div class="page-toolbar">
      <div class="search-group">
        <el-input v-model="search.user_id" placeholder="用户ID" clearable @change="fetchData" />
        <el-select v-model="search.log_type" placeholder="日志类型" clearable @change="fetchData">
          <el-option label="登录" value="登录" />
          <el-option label="选课" value="选课" />
          <el-option label="成绩" value="成绩" />
          <el-option label="系统" value="系统" />
        </el-select>
      </div>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="log_id" label="ID" width="70" />
      <el-table-column prop="log_time" label="时间" width="170">
        <template #default="{ row }">{{ row.log_time?.slice(0, 19) }}</template>
      </el-table-column>
      <el-table-column prop="user_id" label="用户" width="110" />
      <el-table-column label="类型" width="80">
        <template #default="{ row }"><el-tag size="small">{{ row.log_type }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="operation" label="操作描述" min-width="220" show-overflow-tooltip />
      <el-table-column label="结果" width="80">
        <template #default="{ row }">
          <span class="status-tag" :class="row.result === '成功' ? 'status-approved' : 'status-rejected'">
            {{ row.result }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="ip_address" label="IP" width="140" />
    </el-table>

    <el-pagination
      v-model:current-page="page" :total="total" :page-size="50"
      layout="total, prev, pager, next" @current-change="fetchData"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '@/utils/request'

const loading = ref(false), page = ref(1), total = ref(0), list = ref([])
const search = reactive({ user_id: '', log_type: '' })

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/admin/logs', { params: { page: page.value, ...search } })
    list.value = res.data?.data || []; total.value = res.data?.total || 0
  } finally { loading.value = false }
}
</script>
