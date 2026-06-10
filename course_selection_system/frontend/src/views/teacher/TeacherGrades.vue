<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">成绩录入</h3>
      <div class="search-group">
        <el-select v-model="selectedPlan" placeholder="选择课程" style="width:280px" @change="fetchData">
          <el-option v-for="p in plans" :key="p.plan_id" :label="`${p.course_id} - ${p.semester}`" :value="p.plan_id" />
        </el-select>
        <el-upload :show-file-list="false" :before-upload="uploadExcel" accept=".xlsx" v-if="selectedPlan">
          <el-button type="warning">批量导入 Excel</el-button>
        </el-upload>
      </div>
    </div>

    <el-table :data="students" stripe v-loading="loading" v-if="selectedPlan">
      <el-table-column prop="student_id" label="学号" width="130" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column label="成绩" width="140">
        <template #default="{ row }">
          <template v-if="row.grade_status === '未录入'">
            <el-input-number v-model="row._score" :min="0" :max="100" size="small" style="width:100px"
              placeholder="0-100" />
          </template>
          <el-tag v-else :type="row.score >= 60 ? 'success' : 'danger'" effect="dark">{{ row.score }}</el-tag>
          <span v-if="row.gpa_point != null" style="margin-left:4px;color:#909399;font-size:12px">GPA:{{ row.gpa_point }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="grade_status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.grade_status === '正常' ? 'success' : row.grade_status === '待审核' ? 'warning' : 'info'">
            {{ row.grade_status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90">
        <template #default="{ row }">
          <el-button size="small" type="primary" :disabled="row.grade_status !== '未录入'" @click="submitGrade(row)">
            保存
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-else description="请选择一门课程" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const plans = ref([])
const selectedPlan = ref(null)
const students = ref([])

onMounted(async () => {
  const res = await request.get('/teacher/plans')
  plans.value = res.data?.items || []
})

async function fetchData() {
  if (!selectedPlan.value) { students.value = []; return }
  loading.value = true
  try {
    const res = await request.get('/teacher/grades', { params: { plan_id: selectedPlan.value } })
    students.value = (res.data?.items || []).map(s => ({ ...s, _score: null }))
  } finally { loading.value = false }
}

async function submitGrade(row) {
  if (row._score == null) { ElMessage.warning('请输入成绩'); return }
  await request.post('/grade/record', {
    student_id: row.student_id,
    plan_id: selectedPlan.value,
    score: row._score,
  })
  ElMessage.success('成绩录入成功')
  fetchData()
}

async function uploadExcel(file) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('plan_id', selectedPlan.value)
  const res = await request.post('/grade/batch', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  ElMessage.success(`导入完成: 成功 ${res.data.success_count}，失败 ${res.data.fail_count}`)
  fetchData()
  return false
}
</script>
