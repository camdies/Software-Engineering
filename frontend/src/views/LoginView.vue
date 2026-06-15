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
        <el-form-item style="text-align:center;margin-bottom:0">
          <el-button link type="primary" @click="showForgot = true">忘记密码</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 忘记密码弹窗 -->
    <el-dialog v-model="showForgot" title="找回密码" width="460px">
      <p style="color:#909399;margin:0 0 16px;font-size:13px;line-height:1.8">
        输入您的账号提交密码重置申请，管理员审核通过后密码将重置为默认密码 <strong>123456</strong>。
        审核需要一定时间，请耐心等待。
      </p>
      <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules">
        <el-form-item prop="user_id">
          <el-input v-model="forgotForm.user_id" placeholder="请输入您的账号（学号/工号）" size="large" />
        </el-form-item>
        <el-form-item prop="reason">
          <el-input v-model="forgotForm.reason" type="textarea" :rows="3" placeholder="请简要说明申请重置密码的原因，以便管理员审核" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForgot = false">取消</el-button>
        <el-button type="primary" :loading="forgotLoading" @click="submitForgot">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import request from '@/utils/request'

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
    const res = await auth.login(form.user_id, form.password)
    if (!res || !res.success) {
      // Backend returned an error — interceptor already showed ElMessage.
      // Don't navigate, just let the user try again.
      return
    }
    if (auth.isAdmin) router.push('/admin/students')
    else if (auth.isTeacher) router.push('/teacher/plans')
    else router.push('/student/enroll')
  } catch (_) {
    // network error — interceptor already showed ElMessage.error
  } finally {
    loading.value = false
  }
}

// ── 忘记密码 ──
const showForgot = ref(false)
const forgotLoading = ref(false)
const forgotFormRef = ref(null)
const forgotForm = reactive({ user_id: '', reason: '' })
const forgotRules = {
  user_id: [{ required: true, message: '请输入账号', trigger: 'blur' }],
}

async function submitForgot() {
  const valid = await forgotFormRef.value.validate().catch(() => false)
  if (!valid) return
  forgotLoading.value = true
  try {
    await request.post('/auth/forgot-password', forgotForm)
    ElMessage.success('密码重置申请已提交，请等待管理员审核')
    showForgot.value = false
  } catch (_) { /* interceptor handles */ }
  finally { forgotLoading.value = false }
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
