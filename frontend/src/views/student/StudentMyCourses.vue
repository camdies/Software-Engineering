<template>
  <div class="page-card">
    <h3 style="margin:0 0 12px">我的课程</h3>
    <el-table :data="courses" stripe v-loading="loading" empty-text="暂未选课">
      <el-table-column prop="course_id" label="课程代码" width="110" />
      <el-table-column prop="course_name" label="课程名称" min-width="160" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column prop="time_slot" label="上课时间" width="130" />
      <el-table-column prop="enroll_time" label="选课时间" width="170" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button type="danger" size="small" @click="drop(row)">退课</el-button>
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

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/student/my-courses')
    courses.value = res.data?.items || []
  } finally { loading.value = false }
}

async function drop(row) {
  try {
    await ElMessageBox.confirm(`确认退选 "${row.course_name}"？`, '退课确认', { type: 'warning' })
  } catch { return }

  const res = await request.post('/enrollment/drop', { plan_id: row.plan_id })
  if (res.success) {
    ElMessage.success(res.message)
    fetchData()
  }
}
</script>
