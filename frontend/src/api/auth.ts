import apiClient from '@/api/client'
import { clearStoredToken, setStoredToken } from '@/api/token'
import type { AuthUser, LoginRequest, TokenResponse } from '@/types/auth'

export { clearStoredToken, getStoredToken } from '@/api/token'

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', payload)
  setStoredToken(data.access_token)
  return data
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await apiClient.get<AuthUser>('/api/v1/auth/me')
  return data
}

export function logout(): void {
  clearStoredToken()
}
