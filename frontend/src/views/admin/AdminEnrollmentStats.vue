<template>
  <div class="page-card">
    <div class="page-header">
      <h1>选课统计</h1>
      <el-select v-model="semester" placeholder="选择学期" clearable @change="fetchData">
        <el-option v-for="s in semesterOptions" :key="s" :label="s" :value="s" />
      </el-select>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="plan_id" label="ID" width="70" />
      <el-table-column prop="course_id" label="课程代码" width="110" />
      <el-table-column prop="course_name" label="课程名称" min-width="160" />
      <el-table-column prop="teacher_id" label="教师" width="100" />
      <el-table-column prop="semester" label="学期" width="120" />
      <el-table-column label="选课情况" min-width="220">
        <template #default="{ row }">
          <el-progress
            :percentage="row.capacity ? Math.round(row.enrolled / row.capacity * 100) : 0"
            :stroke-width="14"
            :status="row.enrolled >= row.capacity ? 'exception' : ''"
            :format="() => `${row.enrolled} / ${row.capacity}`"
          />
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
    const res = await request.get('/admin/enrollment-stats', { params })
    list.value = res.data?.items || []
  } finally { loading.value = false }
}
</script>
