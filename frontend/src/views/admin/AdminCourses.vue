<template>
  <div class="page-card">
    <div class="page-header">
      <h1>课程管理</h1>
      <el-button type="primary" @click="openDialog()">新增课程</el-button>
    </div>

    <div class="page-toolbar">
      <div class="search-group">
        <el-input v-model="search.course_id" placeholder="课程代码" clearable @change="fetchData" />
        <el-input v-model="search.course_name" placeholder="课程名称" clearable @change="fetchData" />
      </div>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="course_id" label="课程代码" width="120" />
      <el-table-column prop="course_name" label="课程名称" min-width="180" />
      <el-table-column prop="credit" label="学分" width="70" />
      <el-table-column prop="hours" label="学时" width="70" />
      <el-table-column prop="exam_type" label="考核方式" width="90" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="del(row.course_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page" :total="total" :page-size="20"
      layout="total, prev, pager, next" @current-change="fetchData"
    />

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑课程' : '新增课程'" width="480px">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="课程代码" required>
          <el-input v-model="form.course_id" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="课程名称" required><el-input v-model="form.course_name" /></el-form-item>
        <el-form-item label="学分"><el-input-number v-model="form.credit" :min="0" :max="10" :step="0.5" /></el-form-item>
        <el-form-item label="学时"><el-input-number v-model="form.hours" :min="0" :max="200" /></el-form-item>
        <el-form-item label="考核方式">
          <el-select v-model="form.exam_type" style="width:100%">
            <el-option label="考试" value="考试" />
            <el-option label="考查" value="考查" />
          </el-select>
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
const page = ref(1), total = ref(0), list = ref([])
const search = reactive({ course_id: '', course_name: '' })
const formRef = ref(null)
const form = reactive({ course_id: '', course_name: '', credit: 3, hours: 48, exam_type: '考试' })

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/admin/courses', { params: { page: page.value, ...search } })
    list.value = res.data?.data || []; total.value = res.data?.total || 0
  } finally { loading.value = false }
}

function openDialog(row) {
  editing.value = row || null
  Object.assign(form, row
    ? { course_id: row.course_id, course_name: row.course_name, credit: row.credit, hours: row.hours, exam_type: row.exam_type || '考试' }
    : { course_id: '', course_name: '', credit: 3, hours: 48, exam_type: '考试' })
  dialogVisible.value = true
}

async function save() {
  if (!form.course_id || !form.course_name) { ElMessage.warning('课程代码和名称必填'); return }
  saving.value = true
  try {
    if (editing.value) {
      await request.put(`/admin/courses/${editing.value.course_id}`, form)
    } else {
      await request.post('/admin/courses', form)
    }
    ElMessage.success(editing.value ? '更新成功' : '创建成功')
    dialogVisible.value = false; fetchData()
  } finally { saving.value = false }
}

async function del(id) {
  try { await ElMessageBox.confirm(`确认删除课程 ${id}？`, '确认删除', { type: 'warning' }) } catch { return }
  await request.delete(`/admin/courses/${id}`)
  ElMessage.success('已删除'); fetchData()
}
</script>
