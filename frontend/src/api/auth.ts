import client from './client'
import type { UserInfo } from '@/stores/authStore'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserInfo
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export interface LoginPayload {
  username: string
  password: string
}

export const authApi = {
  register: (data: RegisterPayload) => client.post<UserInfo>('/auth/register', data).then((r) => r.data),
  login: (data: LoginPayload) => client.post<TokenResponse>('/auth/login', data).then((r) => r.data),
  me: () => client.get<UserInfo>('/auth/me').then((r) => r.data),
  logout: (refreshToken: string) =>
    client.post<void>('/auth/logout', { refresh_token: refreshToken }),
}
