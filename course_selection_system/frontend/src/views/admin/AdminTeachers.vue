<template>
  <div class="page-card">
    <div class="page-toolbar">
      <div class="search-group">
        <el-input v-model="search.teacher_id" placeholder="工号" clearable style="width:130px" @change="fetchData" />
        <el-input v-model="search.name" placeholder="姓名" clearable style="width:130px" @change="fetchData" />
        <el-input v-model="search.college" placeholder="学院" clearable style="width:130px" @change="fetchData" />
      </div>
      <el-button type="primary" @click="openDialog()">新增教师</el-button>
    </div>

    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="teacher_id" label="工号" width="130" />
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="college" label="学院" min-width="160" />
      <el-table-column prop="contact" label="联系方式" width="140" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="del(row.teacher_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="total, prev, pager, next"
      @current-change="fetchData" />

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑教师' : '新增教师'" width="460px">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="工号" required>
          <el-input v-model="form.teacher_id" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="姓名" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="学院"><el-input v-model="form.college" /></el-form-item>
        <el-form-item label="联系方式"><el-input v-model="form.contact" /></el-form-item>
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
const search = reactive({ teacher_id: '', name: '', college: '' })
const formRef = ref(null)
const form = reactive({ teacher_id: '', name: '', college: '', contact: '' })

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const res = await request.get('/admin/teachers', { params: { page: page.value, ...search } })
    list.value = res.data?.data || []; total.value = res.data?.total || 0
  } finally { loading.value = false }
}

function openDialog(row) {
  editing.value = row || null
  Object.assign(form, row ? { teacher_id: row.teacher_id, name: row.name, college: row.college || '', contact: row.contact || '' }
    : { teacher_id: '', name: '', college: '', contact: '' })
  dialogVisible.value = true
}

async function save() {
  if (!form.teacher_id || !form.name) { ElMessage.warning('工号和姓名必填'); return }
  saving.value = true
  try {
    if (editing.value) {
      await request.put(`/admin/teachers/${editing.value.teacher_id}`, form)
    } else {
      await request.post('/admin/teachers', form)
    }
    ElMessage.success(editing.value ? '更新成功' : '创建成功')
    dialogVisible.value = false; fetchData()
  } finally { saving.value = false }
}

async function del(id) {
  try { await ElMessageBox.confirm(`确认删除教师 ${id}？`, '确认删除', { type: 'warning' }) } catch { return }
  await request.delete(`/admin/teachers/${id}`)
  ElMessage.success('已删除'); fetchData()
}
</script>
