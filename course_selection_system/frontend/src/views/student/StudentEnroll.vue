<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">可选课程</h3>
      <el-select v-model="semester" placeholder="选择学期" clearable style="width:180px" @change="fetchData">
        <el-option label="2025-1" value="2025-1" />
        <el-option label="2025-2" value="2025-2" />
        <el-option label="2024-1" value="2024-1" />
        <el-option label="2024-2" value="2024-2" />
      </el-select>
    </div>

    <el-table :data="courses" stripe v-loading="loading">
      <el-table-column prop="course_id" label="课程代码" width="110" />
      <el-table-column prop="course_name" label="课程名称" min-width="160" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column prop="teacher_id" label="教师" width="100" />
      <el-table-column prop="time_slot" label="上课时间" width="130" />
      <el-table-column prop="location" label="地点" width="100" />
      <el-table-column label="容量" width="100">
        <template #default="{ row }">
          <el-progress :percentage="Math.round(row.enrolled / row.capacity * 100)" :stroke-width="8"
            :status="row.available > 0 ? '' : 'exception'"
            :format="() => `${row.enrolled}/${row.capacity}`" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" :disabled="row.available <= 0" @click="enroll(row)">选课</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const courses = ref([])
const semester = ref('')

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params = {}
    if (semester.value) params.semester = semester.value
    const res = await request.get('/student/courses', { params })
    courses.value = res.data?.items || []
  } finally { loading.value = false }
}

async function enroll(row) {
  try {
    await ElMessageBox.confirm(`确认选择 "${row.course_name}"？`, '选课确认')
  } catch { return }

  const res = await request.post('/enrollment/select', { plan_id: row.plan_id })
  if (res.success) {
    ElMessage.success(res.message)
    fetchData()
  }
}
</script>
