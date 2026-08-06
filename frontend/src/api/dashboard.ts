import apiClient from '@/api/client'
import { getStoredToken } from '@/api/token'
import type {
  AnalyticsDashboard,
  DashboardNotificationsResponse,
  DashboardStats,
  RecruiterCommandData,
  RecruiterPerformancePeriod,
  RecruiterPerformanceResponse,
} from '@/types/dashboard'
import type { CommandCenterData, CommandCenterFilters } from '@/types/commandCenter'

export async function fetchAnalyticsDashboard(params?: {
  start?: string
  end?: string
}): Promise<AnalyticsDashboard> {
  const { data } = await apiClient.get<AnalyticsDashboard>('/api/v1/dashboard/analytics', {
    params,
  })
  return data
}

export async function fetchRecruiterCommand(params?: {
  start?: string
  end?: string
}): Promise<RecruiterCommandData> {
  const { data } = await apiClient.get<RecruiterCommandData>(
    '/api/v1/dashboard/recruiter-command',
    { params },
  )
  return data
}

export async function fetchDashboardNotifications(
  limit = 12,
): Promise<DashboardNotificationsResponse> {
  const { data } = await apiClient.get<DashboardNotificationsResponse>(
    '/api/v1/dashboard/notifications',
    { params: { limit } },
  )
  return data
}

export async function fetchRecruiterPerformance(params?: {
  period?: RecruiterPerformancePeriod
  industry?: string
}): Promise<RecruiterPerformanceResponse> {
  const { data } = await apiClient.get<RecruiterPerformanceResponse>(
    '/api/v1/dashboard/recruiter-performance',
    { params },
  )
  return data
}

export async function fetchCommandCenter(
  params?: CommandCenterFilters,
): Promise<CommandCenterData> {
  const { data } = await apiClient.get<CommandCenterData>('/api/v1/dashboard/command-center', {
    params,
  })
  return data
}

/** @deprecated prefer fetchAnalyticsDashboard */
export async function fetchDashboardStats(params?: {
  start?: string
  end?: string
}): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>('/api/v1/dashboard/stats', { params })
  return data
}

export function buildDashboardWsUrl(): string {
  const token = getStoredToken() ?? ''
  const base = import.meta.env.VITE_API_BASE_URL || window.location.origin
  const url = new URL('/api/v1/dashboard/ws', base)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.searchParams.set('token', token)
  return url.toString()
}
