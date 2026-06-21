import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE = (typeof __API_BASE__ !== 'undefined') ? __API_BASE__ : '/api'

const request = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

let _redirecting = false

function redirectToLogin() {
  if (_redirecting) return
  _redirecting = true
  // Import router lazily to avoid circular dependency at module init time.
  // At runtime the router is always installed before any request fires.
  import('@/router').then(({ default: router }) => {
    router.push('/login').catch(() => {
      window.location.href = '/login'
    })
  }).catch(() => {
    window.location.href = '/login'
  })
  // Belt-and-suspenders: if the dynamic import hangs (should never happen),
  // fall back to hard redirect after 800ms.
  setTimeout(() => {
    if (_redirecting) {
      window.location.href = '/login'
    }
  }, 800)
}

export function resetRedirectFlag() {
  _redirecting = false
}

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

request.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.success === false && data.message) {
      ElMessage.error(data.message)
    }
    return data
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      const msg = error.response.data?.message
      if (status === 401) {
        if (!_redirecting) {
          ElMessage.error(msg || '登录已过期，请重新登录')
          localStorage.removeItem('token')
          localStorage.removeItem('role')
          localStorage.removeItem('user_id')
          redirectToLogin()
        }
        // If already redirecting, silently reject — don't stack messages or navigations.
        return Promise.reject(error)
      } else if (status === 403) {
        ElMessage.error(msg || '权限不足')
      } else {
        ElMessage.error(msg || '服务器错误')
      }
    } else {
      ElMessage.error('网络异常')
    }
    return Promise.reject(error)
  },
)

export default request
