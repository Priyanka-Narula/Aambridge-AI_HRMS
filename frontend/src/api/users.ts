import apiClient from '@/api/client'
import type { RecruiterCreatePayload, RecruiterListItem, RecruiterUpdatePayload } from '@/types/auth'

export async function fetchUsers(): Promise<RecruiterListItem[]> {
  const { data } = await apiClient.get<RecruiterListItem[]>('/api/v1/users/')
  return data
}

export async function fetchUser(userId: string): Promise<RecruiterListItem> {
  const { data } = await apiClient.get<RecruiterListItem>(`/api/v1/users/${userId}`)
  return data
}

export async function createRecruiter(payload: RecruiterCreatePayload): Promise<RecruiterListItem> {
  const { data } = await apiClient.post<RecruiterListItem>('/api/v1/users/recruiters', payload)
  return data
}

export async function updateRecruiter(userId: string, payload: RecruiterUpdatePayload): Promise<RecruiterListItem> {
  const { data } = await apiClient.put<RecruiterListItem>(`/api/v1/users/${userId}`, payload)
  return data
}

export async function updateUserStatus(userId: string, status: 'active' | 'inactive'): Promise<RecruiterListItem> {
  const { data } = await apiClient.patch<RecruiterListItem>(`/api/v1/users/${userId}/status`, { status })
  return data
}
