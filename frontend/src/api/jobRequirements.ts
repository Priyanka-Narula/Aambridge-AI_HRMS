import apiClient from '@/api/client'
import type {
  JobRequirementCreatePayload,
  JobRequirementListItem,
  JobRequirementStatus,
  JobRequirementUpdatePayload,
} from '@/types/jobRequirement'

export async function fetchJobRequirements(): Promise<JobRequirementListItem[]> {
  const { data } = await apiClient.get<JobRequirementListItem[]>('/api/v1/job-requirements/')
  return data
}

export async function fetchJobRequirement(id: string): Promise<JobRequirementListItem> {
  const { data } = await apiClient.get<JobRequirementListItem>(`/api/v1/job-requirements/${id}`)
  return data
}

export async function createJobRequirement(
  payload: JobRequirementCreatePayload,
): Promise<JobRequirementListItem> {
  const { data } = await apiClient.post<JobRequirementListItem>('/api/v1/job-requirements/', payload)
  return data
}

export async function updateJobRequirement(
  id: string,
  payload: JobRequirementUpdatePayload,
): Promise<JobRequirementListItem> {
  const { data } = await apiClient.put<JobRequirementListItem>(
    `/api/v1/job-requirements/${id}`,
    payload,
  )
  return data
}

export async function updateJobRequirementStatus(
  id: string,
  status: JobRequirementStatus,
): Promise<JobRequirementListItem> {
  const { data } = await apiClient.patch<JobRequirementListItem>(
    `/api/v1/job-requirements/${id}/status`,
    { status },
  )
  return data
}
