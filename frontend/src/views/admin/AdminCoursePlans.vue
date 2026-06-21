<template>
  <div class="page-card">
    <div class="page-header">
      <h1>开课计划</h1>
      <el-select v-model="semester" placeholder="选择学期" clearable @change="fetchData">
        <el-option v-for="s in semesterOptions" :key="s" :label="s" :value="s" />
      </el-select>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="plan_id" label="ID" width="70" />
      <el-table-column prop="course_id" label="课程代码" width="110" />
      <el-table-column prop="course_name" label="课程名称" min-width="150" />
      <el-table-column prop="teacher_id" label="教师" width="100" />
      <el-table-column prop="semester" label="学期" width="120" />
      <el-table-column prop="time_slot" label="上课时间" min-width="140" />
      <el-table-column prop="location" label="地点" width="110" />
      <el-table-column label="容量" width="100">
        <template #default="{ row }">{{ row.enrolled || 0 }} / {{ row.capacity }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <span class="status-tag" :class="statusClass(row.status)">{{ row.status }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const loading = ref(false), list = ref([]), semester = ref('')
const semesterOptions = ['2026-2027-1', '2025-2026-2', '2025-2026-1']

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params = {}
    if (semester.value) params.semester = semester.value
    const res = await request.get('/admin/course-plans', { params })
    list.value = res.data?.items || []
  } finally { loading.value = false }
}

function statusClass(s) {
  if (s === '已通过') return 'status-approved'
  if (s === '待审核') return 'status-pending'
  if (s === '已驳回') return 'status-rejected'
  return 'status-default'
}
</script>
