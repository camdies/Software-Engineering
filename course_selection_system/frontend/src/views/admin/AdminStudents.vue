<template>
  <div class="page-card">
    <div class="page-toolbar">
      <div class="search-group">
        <el-input v-model="search.student_id" placeholder="学号" clearable style="width:130px" @change="fetchData" />
        <el-input v-model="search.name" placeholder="姓名" clearable style="width:130px" @change="fetchData" />
        <el-input v-model="search.class_name" placeholder="班级" clearable style="width:130px" @change="fetchData" />
      </div>
      <el-button type="primary" @click="openDialog()">新增学生</el-button>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="student_id" label="学号" width="130" />
      <el-table-column prop="name" label="姓名" width="90" />
      <el-table-column prop="grade" label="年级" width="70" />
      <el-table-column prop="major" label="专业" width="120" />
      <el-table-column prop="class_name" label="班级" width="100" />
      <el-table-column prop="email" label="邮箱" min-width="160" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="del(row.student_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next"
      @current-change="fetchData" />

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑学生' : '新增学生'" width="520px">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="学号" required>
          <el-input v-model="form.student_id" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="姓名" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="年级"><el-input v-model="form.grade" placeholder="如 2024" /></el-form-item>
        <el-form-item label="专业"><el-input v-model="form.major" /></el-form-item>
        <el-form-item label="班级"><el-input v-model="form.class_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="联系方式"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item v-if="!editing" label="默认密码">
          <el-input v-model="form.setup_password" show-password placeholder="默认123456" />
          <span style="font-size:11px;color:#909399">系统自动以此学号注册账号</span>
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
const search = reactive({ student_id: '', name: '', class_name: '' })
const formRef = ref(null)
const form = reactive({ student_id: '', name: '', major: '', class_name: '', grade: '', email: '', contact: '', setup_password: '123456' })

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, ...search }
    const res = await request.get('/admin/students', { params })
    list.value = res.data?.data || []; total.value = res.data?.total || 0
  } finally { loading.value = false }
}

function openDialog(row) {
  editing.value = row || null
  if (row) {
    Object.assign(form, { student_id: row.student_id, name: row.name, major: row.major || '', class_name: row.class_name || '', grade: row.grade || '', email: row.email || '', contact: row.contact || '', setup_password: '' })
  } else {
    Object.assign(form, { student_id: '', name: '', major: '', class_name: '', grade: '', email: '', contact: '', setup_password: '123456' })
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.student_id || !form.name) { ElMessage.warning('学号和姓名必填'); return }
  saving.value = true
  try {
    if (editing.value) {
      await request.put(`/admin/students/${editing.value.student_id}`, form)
    } else {
      await request.post('/admin/students', form)
    }
    ElMessage.success(editing.value ? '更新成功' : '学生创建成功，账号已自动注册')
    dialogVisible.value = false; fetchData()
  } finally { saving.value = false }
}

async function del(id) {
  try { await ElMessageBox.confirm(`确认删除学生 ${id}？`, '确认删除', { type: 'warning' }) } catch { return }
  await request.delete(`/admin/students/${id}`)
  ElMessage.success('已删除'); fetchData()
}
</script>
