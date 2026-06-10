import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截器：附加 JWT
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理
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
        ElMessage.error(msg || '登录已过期，请重新登录')
        localStorage.removeItem('token')
        localStorage.removeItem('role')
        localStorage.removeItem('user_id')
        window.location.href = '/login'
      } else if (status === 403) {
        ElMessage.error(msg || '无权执行此操作')
      } else {
        ElMessage.error(msg || '服务器异常')
      }
    } else {
      ElMessage.error('网络连接异常')
    }
    return Promise.reject(error)
  }
)

export default request
