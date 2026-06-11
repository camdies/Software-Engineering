<template>
  <div class="page-card">
    <h3 style="margin:0 0 16px">审核中心</h3>
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- 密码重置审核 -->
      <el-tab-pane label="密码重置" name="password">
        <el-table :data="pwdList" stripe v-loading="pwdLoading" empty-text="暂无待审核申请">
          <el-table-column prop="request_id" label="ID" width="60" />
          <el-table-column prop="user_id" label="账号" width="120" />
          <el-table-column prop="reason" label="原因" min-width="180" />
          <el-table-column prop="request_time" label="申请时间" width="170">
            <template #default="{ row }">{{ row.request_time?.slice(0, 19) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-input v-model="row._comment" size="small" placeholder="审核意见" style="width:100px" />
              <el-button size="small" type="success" @click="handlePwd(row, 'approve')">通过</el-button>
              <el-button size="small" type="danger" @click="handlePwd(row, 'reject')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 成绩修改审核 -->
      <el-tab-pane label="成绩修改" name="grade">
        <el-table :data="gradeList" stripe v-loading="gradeLoading" empty-text="暂无待审核成绩">
          <el-table-column prop="grade_id" label="ID" width="60" />
          <el-table-column prop="student_id" label="学号" width="120" />
          <el-table-column prop="course_name" label="课程" width="140" />
          <el-table-column label="当前成绩" width="80">
            <template #default="{ row }"><el-tag>{{ row.score }}</el-tag></template>
          </el-table-column>
          <el-table-column label="申请改为" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.new_score" type="warning">{{ row.new_score }}</el-tag>
              <span v-else>--</span>
            </template>
          </el-table-column>
          <el-table-column prop="modify_reason" label="修改原因" min-width="150" />
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-input v-model="row._comment" size="small" placeholder="审核意见" style="width:100px" />
              <el-button size="small" type="success" @click="handleGrade(row, 'approve')">通过</el-button>
              <el-button size="small" type="danger" @click="handleGrade(row, 'reject')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 授课计划审核 -->
      <el-tab-pane label="课程审核" name="plan">
        <el-table :data="planList" stripe v-loading="planLoading" empty-text="暂无待审核计划">
          <el-table-column prop="plan_id" label="ID" width="60" />
          <el-table-column prop="course_id" label="课程代码" width="90" />
          <el-table-column prop="course_name" label="课程名" width="130" />
          <el-table-column prop="teacher_id" label="教师" width="80" />
          <el-table-column prop="teacher_name" label="教师名" width="90" />
          <el-table-column prop="time_slot" label="时间安排" width="190" />
          <el-table-column prop="location" label="地点" width="100" />
          <el-table-column prop="capacity" label="容量" width="60" />
          <el-table-column prop="apply_reason" label="申请理由" min-width="160" show-overflow-tooltip />
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-input v-model="row._comment" size="small" placeholder="审核意见" style="width:100px" />
              <el-button size="small" type="success" @click="handlePlan(row, 'approve')">通过</el-button>
              <el-button size="small" type="danger" @click="handlePlan(row, 'reject')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 待处理数量 -->
    <div style="margin-top:16px;display:flex;gap:16px">
      <el-tag type="danger">密码重置: {{ badge.pwd }}</el-tag>
      <el-tag type="warning">成绩修改: {{ badge.grade }}</el-tag>
      <el-tag type="info">课程审核: {{ badge.plan }}</el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const activeTab = ref('password')

const pwdList = ref([]), pwdLoading = ref(false)
const gradeList = ref([]), gradeLoading = ref(false)
const planList = ref([]), planLoading = ref(false)
const badge = reactive({ pwd: 0, grade: 0, plan: 0 })

onMounted(async () => {
  await Promise.all([fetchPwd(), fetchGrade(), fetchPlan(), fetchBadge()])
})

async function fetchBadge() {
  try {
    const res = await request.get('/audit/overview')
    badge.pwd = res.data?.password_resets || 0
    badge.grade = res.data?.grade_modifications || 0
    badge.plan = res.data?.course_plans || 0
  } catch { /* ignore */ }
}

async function fetchPwd() {
  pwdLoading.value = true
  try {
    const res = await request.get('/audit/password-resets')
    pwdList.value = (res.data?.items || []).map(r => ({ ...r, _comment: '' }))
  } finally { pwdLoading.value = false }
}

async function fetchGrade() {
  gradeLoading.value = true
  try {
    const res = await request.get('/admin/grades/pending')
    gradeList.value = (res.data?.items || []).map(r => ({ ...r, _comment: '' }))
  } finally { gradeLoading.value = false }
}

async function fetchPlan() {
  planLoading.value = true
  try {
    const res = await request.get('/audit/course-plans')
    planList.value = (res.data?.items || []).map(r => ({ ...r, _comment: '' }))
  } finally { planLoading.value = false }
}

function onTabChange() { fetchBadge() }

async function handlePwd(row, action) {
  await request.post(`/audit/password-resets/${row.request_id}`, { action, comment: row._comment || '' })
  ElMessage.success(action === 'approve' ? '密码重置已通过' : '已驳回')
  fetchPwd(); fetchBadge()
}

async function handleGrade(row, action) {
  await request.post(`/grade/audit/${row.grade_id}`, { action, comment: row._comment || '' })
  ElMessage.success(action === 'approve' ? '成绩修改已通过' : '已驳回')
  fetchGrade(); fetchBadge()
}

async function handlePlan(row, action) {
  await request.post(`/audit/course-plans/${row.plan_id}`, { action, comment: row._comment || '' })
  ElMessage.success(action === 'approve' ? '授课计划已通过' : '已驳回')
  fetchPlan(); fetchBadge()
}
</script>
