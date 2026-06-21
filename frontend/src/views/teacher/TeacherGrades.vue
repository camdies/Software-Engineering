<template>
  <div class="page-card">
    <div class="page-header">
      <h1>成绩录入</h1>
      <div class="search-group">
        <el-select v-model="selectedPlan" placeholder="选择课程" @change="fetchData">
          <el-option v-for="p in plans" :key="p.plan_id" :label="`${p.course_id} - ${p.course_name} (${p.semester})`" :value="p.plan_id" />
        </el-select>
        <el-upload v-if="selectedPlan" :show-file-list="false" :before-upload="uploadExcel" accept=".xlsx">
          <el-button type="warning" plain>批量导入 Excel</el-button>
        </el-upload>
      </div>
    </div>

    <div v-if="selectedPlan">
      <el-table :data="students" stripe v-loading="loading">
        <el-table-column prop="student_id" label="学号" width="130" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="成绩" width="160">
          <template #default="{ row }">
            <template v-if="row.grade_status === '未录入'">
              <el-input-number v-model="row._score" :min="0" :max="100" size="small" style="width:100px" placeholder="0-100" />
            </template>
            <span v-else>
              <el-tag :type="row.score >= 60 ? 'success' : 'danger'" effect="dark" size="small">{{ row.score }}</el-tag>
              <span v-if="row.gpa_point != null" style="margin-left:6px;font-size:var(--text-scale-2xs);color:var(--neutral-400);font-family:var(--font-mono)">
                GPA {{ row.gpa_point }}
              </span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span class="status-tag" :class="gradeStatusClass(row.grade_status)">{{ row.grade_status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="primary" :disabled="row.grade_status !== '未录入'" @click="submitGrade(row)">
              保存
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">&#128218;</div>
      <div class="empty-title">选择课程开始录入</div>
      <div class="empty-desc">从上方下拉菜单选择一门课程，即可查看学生列表并录入成绩</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false), plans = ref([]), selectedPlan = ref(null), students = ref([])

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
  await request.post('/grade/record', { student_id: row.student_id, plan_id: selectedPlan.value, score: row._score })
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

function gradeStatusClass(s) {
  if (s === '正常') return 'status-approved'
  if (s === '待审核') return 'status-pending'
  return 'status-default'
}
</script>
