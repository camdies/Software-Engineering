import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const role = ref(localStorage.getItem('role') || '')
  const userId = ref(localStorage.getItem('user_id') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')
  const isTeacher = computed(() => role.value === 'teacher')
  const isStudent = computed(() => role.value === 'student')

  async function login(user_id, password) {
    const res = await request.post('/auth/login', { user_id, password })
    if (res.success) {
      const d = res.data
      token.value = d.token
      role.value = d.role
      userId.value = d.user_id
      localStorage.setItem('token', d.token)
      localStorage.setItem('role', d.role)
      localStorage.setItem('user_id', d.user_id)
    }
    return res
  }

  async function logout() {
    try {
      await request.post('/auth/logout')
    } catch (_) { /* ignore */ }
    clearSession()
  }

  function clearSession() {
    token.value = ''
    role.value = ''
    userId.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('user_id')
  }

  return { token, role, userId, isLoggedIn, isAdmin, isTeacher, isStudent, login, logout, clearSession }
})
