<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">选课统计</h3>
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
      <el-table-column prop="course_name" label="课程名称" min-width="150" />
      <el-table-column prop="teacher_id" label="教师" width="100" />
      <el-table-column prop="semester" label="学期" width="100" />
      <el-table-column label="选课情况" width="180">
        <template #default="{ row }">
          <el-progress :percentage="row.capacity ? Math.round(row.enrolled / row.capacity * 100) : 0" :stroke-width="12"
            :status="row.enrolled >= row.capacity ? 'exception' : ''"
            :format="() => `${row.enrolled} / ${row.capacity}`" />
        </template>
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
    const res = await request.get('/admin/enrollment-stats', { params })
    list.value = res.data?.items || []
  } finally { loading.value = false }
}
</script>
