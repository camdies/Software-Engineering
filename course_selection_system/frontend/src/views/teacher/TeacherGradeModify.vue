<template>
  <div class="page-card">
    <h3 style="margin:0 0 12px">成绩修改申请</h3>

    <div class="page-toolbar">
      <el-select v-model="selectedPlan" placeholder="选择课程" style="width:280px" @change="fetchData">
        <el-option v-for="p in plans" :key="p.plan_id" :label="`${p.course_id} - ${p.semester}`" :value="p.plan_id" />
      </el-select>
    </div>

    <el-table :data="students" stripe v-loading="loading" v-if="selectedPlan" empty-text="该课程暂无已录入成绩">
      <el-table-column prop="student_id" label="学号" width="130" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column label="当前成绩" width="100">
        <template #default="{ row }"><el-tag>{{ row.score ?? '--' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="grade_status" label="状态" width="90" />
      <el-table-column label="新成绩" width="140">
        <template #default="{ row }">
          <el-input-number v-model="row._newScore" :min="0" :max="100" size="small" style="width:100px" v-if="row.grade_status === '正常'" />
        </template>
      </el-table-column>
      <el-table-column label="原因" min-width="160">
        <template #default="{ row }">
          <el-input v-model="row._reason" size="small" placeholder="修改原因" v-if="row.grade_status === '正常'" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90">
        <template #default="{ row }">
          <el-button size="small" type="warning" :disabled="row.grade_status !== '正常' || !row._newScore || !row._reason"
            @click="apply(row)">提交</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-else description="请选择课程查看已录入成绩" />
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
    students.value = (res.data?.items || [])
      .filter(s => s.grade_status !== '未录入')
      .map(s => ({ ...s, _newScore: null, _reason: '' }))
  } finally { loading.value = false }
}

async function apply(row) {
  await request.post('/grade/modify', {
    grade_id: row.grade_id,
    new_score: row._newScore,
    reason: row._reason,
  })
  ElMessage.success('修改申请已提交')
  fetchData()
}
</script>
