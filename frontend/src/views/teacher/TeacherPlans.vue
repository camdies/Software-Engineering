<template>
  <div class="page-card">
    <div class="page-toolbar">
      <h3 style="margin:0">授课计划</h3>
      <div class="search-group">
        <el-select v-model="semester" placeholder="选择学期" clearable style="width:180px" @change="fetchData">
          <el-option label="2026-2027-1" value="2026-2027-1" />
          <el-option label="2025-2026-2" value="2025-2026-2" />
          <el-option label="2025-2026-1" value="2025-2026-1" />
        </el-select>
        <el-button type="primary" @click="openDialog()">新增申请</el-button>
      </div>
    </div>

    <el-table :data="filteredPlans" stripe v-loading="loading">
      <el-table-column prop="plan_id" label="ID" width="60" />
      <el-table-column prop="course_id" label="课程代码" width="100" />
      <el-table-column prop="time_slot" label="上课时间" min-width="200" />
      <el-table-column prop="location" label="地点" width="100" />
      <el-table-column prop="capacity" label="容量" width="70" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === '已通过' ? 'success' : row.status === '已驳回' ? 'danger' : row.status === '已停课' ? 'info' : 'warning'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === '待审核'" size="small" @click="openDialog(row)">编辑</el-button>
          <el-button v-if="row.status !== '待审核' && row.status !== '已停课'" size="small" type="warning" @click="stopCourse(row.plan_id)">停课</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '修改申请' : '新增授课申请'" width="620px">
      <el-form ref="formRef" :model="form" label-width="100px">
        <el-form-item label="课程" required>
          <el-select v-model="form.course_id" filterable placeholder="搜索课程代码或名称" style="width:100%" :disabled="!!editing"
            @change="onCourseChange">
            <el-option v-for="c in allCourses" :key="c.course_id" :label="`${c.course_id} - ${c.course_name}`" :value="c.course_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学期" required>
          <el-select v-model="form.semester" style="width:100%">
            <el-option label="2026-2027-1" value="2026-2027-1" />
            <el-option label="2025-2026-2" value="2025-2026-2" />
            <el-option label="2025-2026-1" value="2025-2026-1" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="上课日" required><el-select v-model="form.weekday" style="width:100%">
              <el-option v-for="(n, i) in weekdayNames" :key="i" :label="n" :value="i+1" /></el-select></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="起始节" required><el-select v-model="form.period_start" style="width:100%">
              <el-option v-for="p in 11" :key="p" :label="`第${p}节 (${periodMap[p-1]?.start || ''})`" :value="p" /></el-select></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="节数" required><el-select v-model="form.period_count" style="width:100%">
              <el-option v-for="c in 11" :key="c" :label="`${c}节`" :value="c" /></el-select></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="起始周" required>
              <el-input-number v-model="form.start_week" :min="1" :max="20" style="width:100%" />
              <span style="font-size:11px;color:#909399">教师自由选择起止周</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束周" required>
              <el-input-number v-model="form.end_week" :min="1" :max="20" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="地点"><el-input v-model="form.location" placeholder="如: 教学楼A101" /></el-form-item>
        <el-form-item label="容量"><el-input-number v-model="form.capacity" :min="1" :max="200" style="width:100%" /></el-form-item>
        <el-form-item label="先修课"><el-input v-model="form.prerequisite" placeholder="课程代码，逗号分隔（如 CS100,CS201）" /></el-form-item>
        <el-form-item label="申请理由">
          <el-input v-model="form.apply_reason" type="textarea" :rows="3" placeholder="请说明开设此课程的理由、教学计划安排等，供管理员审核参考" />
        </el-form-item>
        <el-form-item label="预览时间">
          <el-tag>{{ previewTime }}</el-tag>
          <span style="font-size:11px;color:#909399;margin-left:8px">提交后需管理员审核通过方可生效</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const periodMap = [
  { period: 1, start: '08:30' }, { period: 2, start: '09:20' }, { period: 3, start: '10:20' },
  { period: 4, start: '11:10' }, { period: 5, start: '14:30' }, { period: 6, start: '15:20' },
  { period: 7, start: '16:10' }, { period: 8, start: '17:00' }, { period: 9, start: '19:00' },
  { period: 10, start: '19:50' }, { period: 11, start: '20:40' },
]

const loading = ref(false), saving = ref(false), dialogVisible = ref(false), editing = ref(null)
const plans = ref([]), allCourses = ref([]), semester = ref('')
const formRef = ref(null)
const form = reactive({
  course_id: '', semester: '2026-2027-1', weekday: 1, period_start: 1, period_count: 2,
  start_week: 1, end_week: 20, location: '', capacity: 30, prerequisite: '', apply_reason: '',
})

const previewTime = computed(() => {
  const w = weekdayNames[(form.weekday || 1) - 1]
  return `${w} ${form.period_start}-${form.period_start + form.period_count - 1}节 (第${form.start_week}-${form.end_week}周)`
})

const filteredPlans = computed(() => {
  if (!semester.value) return plans.value
  return plans.value.filter(p => p.semester === semester.value)
})

onMounted(async () => {
  const [pRes, cRes] = await Promise.all([
    request.get('/teacher/plans'),
    request.get('/teacher/courses', { params: { page_size: 200 } }),
  ])
  plans.value = pRes.data?.items || []
  allCourses.value = cRes.data?.data || []
})

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/teacher/plans', { params: { semester: semester.value } })
    plans.value = res.data?.items || []
  } finally { loading.value = false }
}

function openDialog(row) {
  editing.value = row || null
  if (row) {
    Object.assign(form, {
      course_id: row.course_id, semester: row.semester, weekday: row.weekday,
      period_start: row.period_start, period_count: row.period_count,
      start_week: row.start_week, end_week: row.end_week,
      location: row.location || '', capacity: row.capacity || 30, prerequisite: row.prerequisite || '',
      apply_reason: row.apply_reason || '',
    })
  } else {
    Object.assign(form, {
      course_id: '', semester: '2026-2027-1', weekday: 1, period_start: 1, period_count: 2,
      start_week: 1, end_week: 20, location: '', capacity: 30, prerequisite: '', apply_reason: '',
    })
  }
  dialogVisible.value = true
}

function onCourseChange() {}

async function save() {
  if (!form.course_id || !form.semester) { ElMessage.warning('请填写必填项'); return }
  saving.value = true
  try {
    if (editing.value) {
      await request.put(`/teacher/course-plan/${editing.value.plan_id}`, form)
    } else {
      await request.post('/teacher/course-plan', form)
    }
    ElMessage.success(editing.value ? '修改成功' : '申请已提交')
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

async function stopCourse(planId) {
  try { await ElMessageBox.confirm('确认停课？', '停课确认', { type: 'warning' }) } catch { return }
  try {
    await request.put(`/teacher/course-plan/${planId}`, { status: '已停课' })
    ElMessage.success('课程已停课')
    fetchData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}
</script>
