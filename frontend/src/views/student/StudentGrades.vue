<template>
  <div class="page-card">
    <div class="page-header">
      <h1>成绩查询</h1>
    </div>

    <el-table :data="grades" stripe v-loading="loading" empty-text="暂无成绩">
      <el-table-column prop="course_name" label="课程名称" min-width="180" />
      <el-table-column prop="semester" label="学期" width="120" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column label="成绩" width="100">
        <template #default="{ row }">
          <el-tag :type="row.score >= 90 ? 'success' : row.score >= 60 ? '' : 'danger'" effect="dark" size="small">
            {{ row.score ?? '--' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="绩点" width="70">
        <template #default="{ row }">
          <span class="text-mono">{{ row.gpa_point ?? '--' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <span class="status-tag" :class="row.status === '正常' ? 'status-approved' : row.status === '待审核' ? 'status-pending' : 'status-default'">
            {{ row.status }}
          </span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const loading = ref(false), grades = ref([])

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/student/grades')
    grades.value = res.data?.items || []
  } finally { loading.value = false }
}
</script>

<style scoped>
.text-mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-size: var(--text-scale-sm); color: var(--neutral-600); }
</style>
