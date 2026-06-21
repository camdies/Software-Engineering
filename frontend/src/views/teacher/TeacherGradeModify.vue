<template>
  <div class="page-card">
    <div class="page-header">
      <h1>成绩修改申请</h1>
      <el-select v-model="selectedPlan" placeholder="选择课程" @change="fetchData">
        <el-option v-for="p in plans" :key="p.plan_id" :label="`${p.course_id} - ${p.course_name} (${p.semester})`" :value="p.plan_id" />
      </el-select>
    </div>

    <div v-if="selectedPlan">
      <el-table :data="students" stripe v-loading="loading" empty-text="该课程暂无已录入成绩">
        <el-table-column prop="student_id" label="学号" width="130" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="当前成绩" width="100">
          <template #default="{ row }"><el-tag size="small">{{ row.score ?? '--' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span class="status-tag" :class="gradeStatusClass(row.grade_status)">{{ row.grade_status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="新成绩" width="140">
          <template #default="{ row }">
            <el-input-number v-if="row.grade_status === '正常'" v-model="row._newScore" :min="0" :max="100" size="small" style="width:100px" />
          </template>
        </el-table-column>
        <el-table-column label="原因" min-width="160">
          <template #default="{ row }">
            <el-input v-if="row.grade_status === '正常'" v-model="row._reason" size="small" placeholder="修改原因" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="warning" :disabled="row.grade_status !== '正常' || !row._newScore || !row._reason" @click="apply(row)">
              提交
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">&#9998;</div>
      <div class="empty-title">选择课程查看成绩</div>
      <div class="empty-desc">从上方下拉菜单选择课程，可对已录入成绩提交修改申请</div>
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
    students.value = (res.data?.items || [])
      .filter(s => s.grade_status !== '未录入')
      .map(s => ({ ...s, _newScore: null, _reason: '' }))
  } finally { loading.value = false }
}

async function apply(row) {
  await request.post('/grade/modify', { grade_id: row.grade_id, new_score: row._newScore, reason: row._reason })
  ElMessage.success('修改申请已提交')
  fetchData()
}

function gradeStatusClass(s) {
  if (s === '正常') return 'status-approved'
  if (s === '待审核') return 'status-pending'
  return 'status-default'
}
</script>
