<template>
  <div>
    <div class="stat-cards">
      <div class="stat-card"><div class="stat-value">{{ stats.total_credits ?? 0 }}</div><div class="stat-label">已修学分</div></div>
      <div class="stat-card success"><div class="stat-value">{{ stats.cumulative_gpa ?? '0.00' }}</div><div class="stat-label">累计 GPA</div></div>
      <div class="stat-card danger"><div class="stat-value">{{ stats.failed_courses?.length ?? 0 }}</div><div class="stat-label">未通过课程</div></div>
    </div>

    <div class="page-card" v-if="stats.failed_courses?.length">
      <h4 style="margin:0 0 12px">未通过课程详情</h4>
      <el-table :data="stats.failed_courses" stripe size="small">
        <el-table-column prop="course_name" label="课程名称" />
        <el-table-column prop="score" label="成绩" width="80" />
        <el-table-column prop="semester" label="学期" width="100" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const stats = ref({ total_credits: 0, cumulative_gpa: 0, failed_courses: [] })

onMounted(async () => {
  const res = await request.get('/student/stats')
  stats.value = res.data || stats.value
})
</script>
