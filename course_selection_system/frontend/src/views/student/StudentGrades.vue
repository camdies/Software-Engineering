<template>
  <div class="page-card">
    <h3 style="margin:0 0 12px">成绩查询</h3>
    <el-table :data="grades" stripe v-loading="loading" empty-text="暂无成绩">
      <el-table-column prop="course_name" label="课程名称" min-width="160" />
      <el-table-column prop="semester" label="学期" width="100" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column label="成绩" width="100">
        <template #default="{ row }">
          <el-tag :type="row.score >= 90 ? 'success' : row.score >= 60 ? '' : 'danger'" effect="dark">
            {{ row.score ?? '--' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="gpa_point" label="绩点" width="70" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === '正常' ? 'success' : row.status === '待审核' ? 'warning' : ''">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'

const loading = ref(false)
const grades = ref([])

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/student/grades')
    grades.value = res.data?.items || []
  } finally { loading.value = false }
}
</script>
