import axios from 'axios'
import { ElMessage } from 'element-plus'

// API base URL — determined at BUILD time by VITE_API_TARGET env var.
// In dev mode (npm run dev), the Vite proxy at /api forwards to the
// actual backend. In production, __API_BASE__ is injected by vite.config.js
// as a full URL (e.g. https://api.your-domain.com).
//
// If neither is set, defaults to '/api' which works when Flask serves
// both frontend and backend from the same origin (legacy mode).
const API_BASE = (typeof __API_BASE__ !== 'undefined') ? __API_BASE__ : '/api'

const request = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
})

// Request interceptor: attach JWT token
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

// Response interceptor: unified error handling
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
        ElMessage.error(msg || 'Login expired, please re-login')
        localStorage.removeItem('token')
        localStorage.removeItem('role')
        localStorage.removeItem('user_id')
        window.location.href = '/login'
      } else if (status === 403) {
        ElMessage.error(msg || 'Permission denied')
      } else {
        ElMessage.error(msg || 'Server error')
      }
    } else {
      ElMessage.error('Network error')
    }
    return Promise.reject(error)
  }
)

export default request
