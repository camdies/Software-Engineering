<template>
  <div class="page-card">
    <h3 style="margin:0 0 16px">选课控制</h3>

    <el-form :model="form" label-width="120px" width="500px">
      <el-form-item label="选课开关">
        <el-switch v-model="form.is_open" active-text="开放" inactive-text="关闭" />
      </el-form-item>
      <el-form-item label="开放时间">
        <el-date-picker v-model="form.open_time" type="datetime" placeholder="选课开放时间" format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss" style="width:280px" />
      </el-form-item>
      <el-form-item label="截止时间">
        <el-date-picker v-model="form.close_time" type="datetime" placeholder="选课截止时间" format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss" style="width:280px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const saving = ref(false)
const form = reactive({ is_open: false, open_time: '', close_time: '' })

onMounted(async () => {
  const res = await request.get('/admin/enrollment-control')
  const d = res.data
  form.is_open = d.is_open
  form.open_time = d.open_time || ''
  form.close_time = d.close_time || ''
})

async function save() {
  saving.value = true
  try {
    await request.post('/admin/enrollment-control', form)
    ElMessage.success('选课时段设置已更新')
  } finally { saving.value = false }
}
</script>
