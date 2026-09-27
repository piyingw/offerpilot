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

function forceLogout() {
  useAuthStore.getState().logout()
  window.location.href = '/login'
}

// 单飞刷新：并发多个 401 只发起一次 /auth/refresh，其余等待结果后重试
let refreshingPromise: Promise<boolean> | null = null

client.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const { response, config } = error
    const { pathname } = window.location
    const isAuthPage = pathname === '/login' || pathname === '/register'
    const isRefreshCall = config?.url === '/auth/refresh'

    if (
      response?.status === 401 &&
      !isAuthPage &&
      !isRefreshCall &&
      useAuthStore.getState().token
    ) {
      refreshingPromise ??= fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: useAuthStore.getState().refreshToken }),
      })
        .then(async (resp) => {
          if (!resp.ok) return false
          const data = await resp.json()
          useAuthStore.getState().setAuth(data.access_token, data.refresh_token, data.user)
          return true
        })
        .catch(() => false)
        .finally(() => {
          refreshingPromise = null
        })

      const refreshed = await refreshingPromise
      if (refreshed) {
        return client(config) // 用新 token 重试原请求
      }
      forceLogout()
    }
    return Promise.reject(error)
  },
)

export default client
