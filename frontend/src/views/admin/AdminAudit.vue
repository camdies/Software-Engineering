<template>
  <div class="page-card">
    <div class="page-header">
      <h1>审核中心</h1>
      <div class="badge-row">
        <span class="stat-chip danger"><span class="chip-dot"></span>密码重置 {{ badge.pwd }}</span>
        <span class="stat-chip warning"><span class="chip-dot"></span>成绩修改 {{ badge.grade }}</span>
        <span class="stat-chip"><span class="chip-dot"></span>课程审核 {{ badge.plan }}</span>
      </div>
    </div>

    <el-alert v-if="auditError" type="error" :closable="false" show-icon class="audit-error">
      <template #title>审核数据加载失败</template>
      {{ auditError.message }}<span v-if="auditError.requestId">（请求ID: {{ auditError.requestId }}）</span>
      <el-button size="small" @click="refreshActive">重试</el-button>
    </el-alert>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="密码重置" name="password">
        <el-table :data="pwdList" stripe v-loading="pwdLoading" empty-text="暂无待审核申请">
          <el-table-column prop="request_id" label="ID" width="60" />
          <el-table-column prop="user_id" label="账号" width="120" />
          <el-table-column prop="reason" label="原因" min-width="180" />
          <el-table-column prop="request_time" label="申请时间" width="170">
            <template #default="{ row }">{{ row.request_time?.slice(0, 19) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-input v-model="row._comment" size="small" placeholder="审核意见" style="width:110px" />
              <el-button size="small" type="success" @click="handlePwd(row, 'approve')">通过</el-button>
              <el-button size="small" type="danger" plain @click="handlePwd(row, 'reject')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="成绩修改" name="grade">
        <el-table :data="gradeList" stripe v-loading="gradeLoading" empty-text="暂无待审核成绩">
          <el-table-column prop="grade_id" label="ID" width="60" />
          <el-table-column prop="student_id" label="学号" width="120" />
          <el-table-column prop="course_name" label="课程" width="140" />
          <el-table-column label="当前成绩" width="90">
            <template #default="{ row }"><el-tag size="small">{{ row.score }}</el-tag></template>
          </el-table-column>
          <el-table-column label="申请改为" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.new_score" type="warning" size="small">{{ row.new_score }}</el-tag>
              <span v-else class="text-muted">--</span>
            </template>
          </el-table-column>
          <el-table-column prop="modify_reason" label="修改原因" min-width="160" show-overflow-tooltip />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-input v-model="row._comment" size="small" placeholder="审核意见" style="width:110px" />
              <el-button size="small" type="success" @click="handleGrade(row, 'approve')">通过</el-button>
              <el-button size="small" type="danger" plain @click="handleGrade(row, 'reject')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="课程审核" name="plan">
        <el-table :data="planList" stripe v-loading="planLoading" empty-text="暂无待审核计划">
          <el-table-column prop="plan_id" label="ID" width="60" />
          <el-table-column prop="course_id" label="课程代码" width="100" />
          <el-table-column prop="course_name" label="课程名" width="140" />
          <el-table-column label="教师" width="140">
            <template #default="{ row }">{{ row.teacher_name || row.teacher_id }}</template>
          </el-table-column>
          <el-table-column prop="time_slot" label="时间安排" min-width="200" />
          <el-table-column prop="location" label="地点" width="110" />
          <el-table-column prop="capacity" label="容量" width="65" />
          <el-table-column prop="apply_reason" label="申请理由" min-width="160" show-overflow-tooltip />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-input v-model="row._comment" size="small" placeholder="审核意见" style="width:110px" />
              <el-button size="small" type="success" @click="handlePlan(row, 'approve')">通过</el-button>
              <el-button size="small" type="danger" plain @click="handlePlan(row, 'reject')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { REFRESH_TTL } from '@/config/refresh-policy'
import { useStaleRefresh } from '@/composables/useStaleRefresh'

const activeTab = ref('password')

const pwdList = ref([]), pwdLoading = ref(false)
const gradeList = ref([]), gradeLoading = ref(false)
const planList = ref([]), planLoading = ref(false)
const badge = reactive({ pwd: 0, grade: 0, plan: 0 })
const auditError = ref(null)

onMounted(async () => {
  await loadData({ force: true }).catch(() => {})
})

async function loadActiveTab() {
  auditError.value = null
  try {
    const loader = { password: fetchPwd, grade: fetchGrade, plan: fetchPlan }[activeTab.value]
    await Promise.all([loader(), fetchBadge()])
  } catch (cause) {
    auditError.value = {
      message: cause.apiError?.message || '无法获取审核数据，请稍后重试',
      requestId: cause.apiError?.request_id || '',
    }
    throw cause
  }
}

const { loadData, invalidate } = useStaleRefresh(loadActiveTab, REFRESH_TTL.audit, 'audit')
function refreshActive() { invalidate(); return loadData({ force: true }).catch(() => {}) }

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

function onTabChange() { refreshActive() }

async function handlePwd(row, action) {
  await request.post(`/audit/password-resets/${row.request_id}`, { action, comment: row._comment || '' })
  ElMessage.success(action === 'approve' ? '密码重置已通过' : '已驳回')
  refreshActive()
}

async function handleGrade(row, action) {
  await request.post(`/grade/audit/${row.grade_id}`, { action, comment: row._comment || '' })
  ElMessage.success(action === 'approve' ? '成绩修改已通过' : '已驳回')
  refreshActive()
}

async function handlePlan(row, action) {
  await request.post(`/audit/course-plans/${row.plan_id}`, { action, comment: row._comment || '' })
  ElMessage.success(action === 'approve' ? '授课计划已通过' : '已驳回')
  refreshActive()
}
</script>

<style scoped>
.badge-row { display: flex; gap: var(--space-4); }
.audit-error { margin-bottom: var(--space-4); }
.stat-chip {
  display: inline-flex; align-items: center; gap: var(--space-2);
  padding: 4px 12px; border-radius: var(--radius-full);
  font-size: var(--text-scale-xs); font-weight: var(--weight-medium);
  background: var(--neutral-100); color: var(--neutral-600);
}
.stat-chip.danger  { background: var(--semantic-danger-bg); color: #991b1b; }
.stat-chip.warning { background: var(--semantic-warning-bg); color: #92400e; }
.chip-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--neutral-400);
}
.stat-chip.danger .chip-dot  { background: var(--semantic-danger); }
.stat-chip.warning .chip-dot { background: var(--semantic-warning); }
</style>
