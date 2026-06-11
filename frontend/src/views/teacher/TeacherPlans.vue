<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">授课计划</h3>
      <el-select v-model="semester" placeholder="选择学期" clearable style="width:180px" @change="fetchData">
        <el-option label="2025-1" value="2025-1" />
        <el-option label="2025-2" value="2025-2" />
        <el-option label="2024-1" value="2024-1" />
        <el-option label="2024-2" value="2024-2" />
      </el-select>
    </div>

    <el-table :data="plans" stripe v-loading="loading">
      <el-table-column prop="plan_id" label="计划ID" width="80" />
      <el-table-column prop="course_id" label="课程代码" width="110" />
      <el-table-column prop="semester" label="学期" width="100" />
      <el-table-column prop="time_slot" label="上课时间" width="130" />
      <el-table-column prop="location" label="地点" width="100" />
      <el-table-column label="选课状态" width="100">
        <template #default="{ row }">
          <span>{{ row.enrolled || 0 }} / {{ row.capacity }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const loading = ref(false)
const plans = ref([])
const semester = ref('')

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params = {}
    if (semester.value) params.semester = semester.value
    const res = await request.get('/teacher/plans', { params })
    plans.value = res.data?.items || []
  } finally { loading.value = false }
}
</script>
