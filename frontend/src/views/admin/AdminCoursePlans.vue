<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">开课计划</h3>
      <el-select v-model="semester" placeholder="选择学期" clearable style="width:180px" @change="fetchData">
        <el-option label="2025-1" value="2025-1" />
        <el-option label="2025-2" value="2025-2" />
        <el-option label="2024-1" value="2024-1" />
        <el-option label="2024-2" value="2024-2" />
      </el-select>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="plan_id" label="计划ID" width="70" />
      <el-table-column prop="course_id" label="课程代码" width="100" />
      <el-table-column prop="course_name" label="课程名称" min-width="140" />
      <el-table-column prop="teacher_id" label="教师" width="100" />
      <el-table-column prop="semester" label="学期" width="100" />
      <el-table-column prop="time_slot" label="上课时间" width="120" />
      <el-table-column prop="location" label="地点" width="90" />
      <el-table-column label="容量" width="90">
        <template #default="{ row }">{{ row.enrolled || 0 }} / {{ row.capacity }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="70">
        <template #default="{ row }"><el-tag size="small">{{ row.status }}</el-tag></template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const loading = ref(false), list = ref([]), semester = ref('')

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
</script>
