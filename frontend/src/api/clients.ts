import apiClient from '@/api/client'
import type { ClientCreatePayload, ClientListItem, ClientUpdatePayload } from '@/types/clients'

export async function fetchClients(): Promise<ClientListItem[]> {
  const { data } = await apiClient.get<ClientListItem[]>('/api/v1/clients/')
  return data
}

export async function createClient(payload: ClientCreatePayload): Promise<ClientListItem> {
  const { data } = await apiClient.post<ClientListItem>('/api/v1/clients/', payload)
  return data
}

export async function fetchClient(id: string): Promise<ClientListItem> {
  const { data } = await apiClient.get<ClientListItem>(`/api/v1/clients/${id}`)
  return data
}

export async function updateClient(id: string, payload: ClientUpdatePayload): Promise<ClientListItem> {
  const { data } = await apiClient.put<ClientListItem>(`/api/v1/clients/${id}`, payload)
  return data
}

export async function updateClientStatus(
  id: string,
  status: 'active' | 'inactive',
): Promise<ClientListItem> {
  const { data } = await apiClient.patch<ClientListItem>(`/api/v1/clients/${id}/status`, { status })
  return data
}
