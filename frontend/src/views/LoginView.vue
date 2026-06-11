<template>
  <div class="login-wrapper">
    <div class="login-card">
      <h1 class="login-title">高校教务管理系统</h1>
      <p class="login-subtitle">Course Selection & Management System</p>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="submit">
        <el-form-item prop="user_id">
          <el-input v-model="form.user_id" placeholder="账号" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="密码" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width:100%" :loading="loading" @click="submit">登 录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref(null)
const loading = ref(false)
const form = reactive({ user_id: '', password: '' })
const rules = {
  user_id: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.login(form.user_id, form.password)
    if (auth.isAdmin) router.push('/admin/students')
    else if (auth.isTeacher) router.push('/teacher/plans')
    else router.push('/student/enroll')
  } catch (_) { /* interceptor handles */ }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a3a5c 0%, #2d6da4 100%);
}
.login-card {
  background: #fff;
  border-radius: 8px;
  padding: 48px 40px 32px;
  width: 400px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.login-title { text-align: center; margin: 0 0 8px; font-size: 24px; color: #303133; }
.login-subtitle { text-align: center; margin: 0 0 32px; font-size: 13px; color: #909399; }
</style>
