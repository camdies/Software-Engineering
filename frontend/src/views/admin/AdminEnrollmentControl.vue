<template>
  <div class="page-card">
    <div class="page-header">
      <h1>选课控制</h1>
      <el-button type="primary" @click="openDialog()">新增时段</el-button>
    </div>

    <div class="page-toolbar">
      <span style="color:var(--neutral-400);font-size:var(--text-scale-sm)">
        选课时段由 semester_config 表控制，每个学期可配置独立的选课时段
      </span>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="semester" label="学期" width="140" />
      <el-table-column prop="total_weeks" label="总周数" width="80" />
      <el-table-column label="学期日期" width="210">
        <template #default="{ row }">{{ row.start_date || '-' }} ~ {{ row.end_date || '-' }}</template>
      </el-table-column>
      <el-table-column label="当前学期" width="95">
        <template #default="{ row }">
          <span class="status-tag" :class="row.is_current ? 'status-approved' : 'status-default'">
            {{ row.is_current ? '是' : '否' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="选课开放" width="95">
        <template #default="{ row }">
          <span class="status-tag" :class="row.enrollment_open ? 'status-approved' : 'status-rejected'">
            {{ row.enrollment_open ? '开放' : '关闭' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="选课时段" min-width="280">
        <template #default="{ row }">
          <span v-if="row.enroll_start && row.enroll_end">{{ row.enroll_start?.replace('T', ' ') }} ~ {{ row.enroll_end?.replace('T', ' ') }}</span>
          <span v-else style="color:var(--neutral-300)">未设置</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="del(row.config_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑选课时段' : '新增选课时段'" width="540px">
      <el-form ref="formRef" :model="form" label-width="100px">
        <el-form-item label="学期标识" required>
          <el-input v-model="form.semester" :disabled="!!editing" placeholder="如 2026-2027-1" />
        </el-form-item>
        <el-form-item label="总周数">
          <el-input-number v-model="form.total_weeks" :min="1" :max="30" />
        </el-form-item>
        <el-form-item label="学期开始日">
          <el-date-picker v-model="form.start_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="学期结束日">
          <el-date-picker v-model="form.end_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="当前学期">
          <el-switch v-model="form.is_current" />
          <span class="form-note">设为当前学期会取消其他学期的"当前"标记</span>
        </el-form-item>
        <el-divider />
        <el-form-item label="选课开放">
          <el-switch v-model="form.enrollment_open" />
        </el-form-item>
        <el-form-item label="选课开始时间">
          <el-date-picker v-model="form.enroll_start" type="datetime" placeholder="选择日期时间" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="选课结束时间">
          <el-date-picker v-model="form.enroll_end" type="datetime" placeholder="选择日期时间" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false), saving = ref(false), dialogVisible = ref(false), editing = ref(null)
const list = ref([])
const formRef = ref(null)
const form = reactive({
  semester: '', total_weeks: 20, start_date: '', end_date: '',
  is_current: false, enrollment_open: false, enroll_start: '', enroll_end: '',
})

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/admin/semester-configs')
    list.value = res.data?.data || []
  } finally { loading.value = false }
}

function openDialog(row) {
  editing.value = row || null
  if (row) {
    Object.assign(form, {
      semester: row.semester, total_weeks: row.total_weeks,
      start_date: row.start_date || '', end_date: row.end_date || '',
      is_current: row.is_current, enrollment_open: row.enrollment_open,
      enroll_start: row.enroll_start || '', enroll_end: row.enroll_end || '',
    })
  } else {
    Object.assign(form, {
      semester: '', total_weeks: 20, start_date: '', end_date: '',
      is_current: false, enrollment_open: false, enroll_start: '', enroll_end: '',
    })
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.semester.trim()) { ElMessage.warning('请输入学期标识'); return }
  saving.value = true
  try {
    const payload = { ...form }
    if (editing.value) {
      await request.put(`/admin/semester-configs/${editing.value.config_id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/semester-configs', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false; fetchData()
  } finally { saving.value = false }
}

async function del(id) {
  try { await ElMessageBox.confirm('确定删除该选课时段配置？', '提示', { type: 'warning' }) } catch { return }
  await request.delete(`/admin/semester-configs/${id}`)
  ElMessage.success('删除成功'); fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.form-note { font-size: var(--text-scale-xs); color: var(--neutral-400); margin-left: var(--space-2); }
</style>
