import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'

const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    // 登录接口本身的 401 不做跳转，只处理"登录态失效"的场景
    const { pathname } = window.location
    const isAuthPage = pathname === '/login' || pathname === '/register'
    if (error.response?.status === 401 && useAuthStore.getState().token && !isAuthPage) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default client
