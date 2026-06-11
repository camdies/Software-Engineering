<template>
  <div class="page-card">
    <h3 style="margin:0 0 12px">成绩审核</h3>
    <el-table :data="list" stripe v-loading="loading" empty-text="暂无待审核成绩">
      <el-table-column prop="grade_id" label="成绩ID" width="70" />
      <el-table-column prop="student_id" label="学号" width="130" />
      <el-table-column prop="course_name" label="课程" width="140" />
      <el-table-column label="当前成绩" width="90">
        <template #default="{ row }"><el-tag>{{ row.score }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="modify_reason" label="修改原因" min-width="160" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-input v-model="row._comment" size="small" placeholder="审核意见" style="width:100px;margin-right:4px" />
          <el-button size="small" type="success" @click="audit(row, 'approve')">通过</el-button>
          <el-button size="small" type="danger" @click="audit(row, 'reject')">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false), list = ref([])

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/admin/grades/pending')
    list.value = (res.data?.items || []).map(item => ({ ...item, _comment: '' }))
  } finally { loading.value = false }
}

async function audit(row, action) {
  await request.post(`/grade/audit/${row.grade_id}`, { action, comment: row._comment || '' })
  ElMessage.success(action === 'approve' ? '已通过' : '已驳回')
  fetchData()
}
</script>
