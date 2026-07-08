import apiClient from '@/api/client'
import { clearStoredToken, setStoredToken } from '@/api/token'
import type { AuthUser, LoginRequest, TokenResponse } from '@/types/auth'

export { clearStoredToken, getStoredToken } from '@/api/token'

export interface UpdateMePayload {
  first_name: string
  last_name: string
  email: string
  phone?: string | null
  location?: string | null
  languages_spoken?: string | null
}

export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', payload)
  setStoredToken(data.access_token)
  return data
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await apiClient.get<AuthUser>('/api/v1/auth/me')
  return data
}

export async function updateMe(payload: UpdateMePayload): Promise<AuthUser> {
  const { data } = await apiClient.put<AuthUser>('/api/v1/auth/me', payload)
  return data
}

export async function changePassword(payload: ChangePasswordPayload): Promise<void> {
  await apiClient.post('/api/v1/auth/change-password', payload)
}

export function logout(): void {
  clearStoredToken()
}
