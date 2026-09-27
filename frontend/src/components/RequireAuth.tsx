import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'

export default function RequireAuth({ children }: { children: ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const location = useLocation()

  // 本地存有 token 但没有用户信息（如清过浏览器数据后半路恢复），校验一次 token 有效性
  useEffect(() => {
    if (token && !user) {
      authApi
        .me()
        .then(setUser)
        .catch(() => {
          // token 失效时由 axios 拦截器统一登出并跳转
        })
    }
  }, [token, user, setUser])

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return <>{children}</>
}
