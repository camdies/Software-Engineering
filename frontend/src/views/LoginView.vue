<template>
  <div class="login-page">
    <!-- Left: brand panel — bright academic vibe -->
    <div class="login-brand">
      <div class="brand-backdrop">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
      </div>
      <div class="brand-content">
        <div class="brand-icon">E</div>
        <h1 class="brand-title">高校教务管理系统</h1>
        <p class="brand-desc">Course Selection & Management System v3.0</p>
        <div class="brand-features">
          <span>课程管理</span>
          <span>成绩分析</span>
          <span>选课系统</span>
          <span>审核中心</span>
        </div>
      </div>
    </div>

    <!-- Right: form -->
    <div class="login-form-area">
      <div class="login-form-card">
        <div class="form-header-icon">&#128214;</div>
        <h2 class="form-title">欢迎回来</h2>
        <p class="form-subtitle">使用您的学号或工号登录系统</p>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="submit">
          <el-form-item prop="user_id">
            <el-input v-model="form.user_id" placeholder="账号" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="密码" :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="login-btn" :loading="loading" @click="submit">
              登 录
            </el-button>
          </el-form-item>
          <el-form-item class="forgot-line">
            <el-button link type="primary" @click="showForgot = true">忘记密码</el-button>
          </el-form-item>
        </el-form>
      </div>
      <p class="login-footer-text">默认密码 123456 &middot; 首次登录建议修改</p>
    </div>

    <!-- Forgot password dialog -->
    <el-dialog v-model="showForgot" title="找回密码" width="440px">
      <p style="color:var(--neutral-500);margin:0 0 16px;font-size:var(--text-scale-sm);line-height:1.8">
        输入您的账号提交密码重置申请，管理员审核通过后密码将重置为 <strong>123456</strong>。
      </p>
      <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules">
        <el-form-item prop="user_id">
          <el-input v-model="forgotForm.user_id" placeholder="请输入您的账号" size="large" />
        </el-form-item>
        <el-form-item prop="reason">
          <el-input v-model="forgotForm.reason" type="textarea" :rows="3" placeholder="请简要说明原因" />
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
import { User, Lock } from '@element-plus/icons-vue'

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
    if (!res || !res.success) return
    if (auth.isAdmin) router.push('/admin/students')
    else if (auth.isTeacher) router.push('/teacher/plans')
    else router.push('/student/enroll')
  } catch (_) { /* interceptor handles */ }
  finally { loading.value = false }
}

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
.login-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ── Brand Panel — Bright Academic ───────────────────────────── */
.login-brand {
  flex: 1;
  position: relative;
  background: linear-gradient(160deg, #eef2ff 0%, #e0f0ff 30%, #f0f5ff 60%, #fdf2f8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.brand-backdrop { position: absolute; inset: 0; }

/* Soft organic blobs for a lively backdrop */
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.45;
  animation: blob-float 18s ease-in-out infinite;
}
.blob-1 {
  width: 360px; height: 360px;
  background: rgba(129, 140, 248, 0.35);
  top: -80px; left: -60px;
  animation-delay: 0s;
}
.blob-2 {
  width: 280px; height: 280px;
  background: rgba(52, 211, 153, 0.28);
  bottom: -60px; right: -40px;
  animation-delay: -6s;
}
.blob-3 {
  width: 220px; height: 220px;
  background: rgba(251, 146, 60, 0.22);
  top: 40%; left: 50%;
  animation-delay: -12s;
}
@keyframes blob-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.06); }
  66% { transform: translate(-20px, 20px) scale(0.94); }
}

.brand-content {
  position: relative;
  text-align: center;
  z-index: 1;
}
.brand-icon {
  width: 80px; height: 80px;
  margin: 0 auto var(--space-6);
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, var(--accent-500), var(--role-admin));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: var(--weight-bold);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.3);
}
.brand-title {
  font-family: var(--font-display);
  font-size: var(--text-scale-2xl);
  font-weight: var(--weight-bold);
  color: var(--neutral-800);
  margin: 0 0 var(--space-2);
  letter-spacing: var(--tracking-tight);
}
.brand-desc {
  font-size: var(--text-scale-sm);
  color: var(--neutral-400);
  margin: 0 0 var(--space-8);
}
.brand-features {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  flex-wrap: wrap;
}
.brand-features span {
  padding: 5px 16px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.7);
  color: var(--neutral-600);
  font-size: var(--text-scale-xs);
  font-weight: var(--weight-medium);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  backdrop-filter: blur(4px);
}

/* ── Form Area ───────────────────────────────────────────────── */
.login-form-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--surface-page);
}
.login-form-card {
  width: 400px;
  background: var(--surface-card);
  border-radius: var(--radius-xl);
  padding: var(--space-10) var(--space-8) var(--space-8);
  box-shadow: 0 4px 24px rgba(99, 102, 241, 0.06), 0 1px 3px rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(99, 102, 241, 0.06);
}
.form-header-icon { text-align: center; font-size: 2.5rem; margin-bottom: var(--space-2); }
.form-title {
  font-family: var(--font-display);
  font-size: var(--text-scale-xl);
  font-weight: var(--weight-bold);
  color: var(--neutral-800);
  margin: 0 0 var(--space-1);
  text-align: center;
  letter-spacing: var(--tracking-tight);
}
.form-subtitle {
  font-size: var(--text-scale-sm);
  color: var(--neutral-400);
  margin: 0 0 var(--space-8);
  text-align: center;
}
.login-btn {
  width: 100%;
  height: 44px;
  font-size: var(--text-scale-base);
  font-weight: var(--weight-semibold);
  letter-spacing: 0.08em;
  background: linear-gradient(135deg, var(--accent-500), var(--role-admin));
  border: none;
}
.login-btn:hover { background: linear-gradient(135deg, var(--accent-600), var(--accent-500)); }
.forgot-line { text-align: center; margin-bottom: 0; }
.login-footer-text {
  margin-top: var(--space-6);
  font-size: var(--text-scale-xs);
  color: var(--neutral-400);
}

@media (max-width: 768px) {
  .login-brand { display: none; }
  .login-form-card { width: 90vw; padding: var(--space-8) var(--space-6); }
}
</style>
