import apiClient from '@/api/client'
import type { CandidateSubmission, OwnerDashboardClient } from '@/types/jobRequirement'

export async function submitCandidate(
  jobRequirementId: string,
  candidateId: string,
  submissionData: Record<string, string>,
): Promise<CandidateSubmission> {
  const { data } = await apiClient.post<CandidateSubmission>(
    `/api/v1/job-requirements/${jobRequirementId}/submissions`,
    { candidate_id: candidateId, submission_data: submissionData },
  )
  return data
}

export async function fetchSubmissions(jobRequirementId: string): Promise<CandidateSubmission[]> {
  const { data } = await apiClient.get<CandidateSubmission[]>(
    `/api/v1/job-requirements/${jobRequirementId}/submissions`,
  )
  return data
}

export async function approveSubmission(
  appId: string,
  action: 'approved' | 'rejected',
  remarks?: string,
): Promise<CandidateSubmission> {
  const { data } = await apiClient.patch<CandidateSubmission>(
    `/api/v1/submissions/${appId}/approve`,
    { action, remarks },
  )
  return data
}

export async function downloadSubmission(appId: string, filename: string): Promise<void> {
  const { data, headers } = await apiClient.get<Blob>(`/api/v1/submissions/${appId}/download`, {
    responseType: 'blob',
  })
  const disposition = headers['content-disposition'] ?? ''
  const match = /filename="?([^"]+)"?/.exec(disposition)
  const resolvedFilename = match?.[1] ?? filename

  const url = URL.createObjectURL(
    new Blob([data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = resolvedFilename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function downloadAllSubmissions(jobRequirementId: string, filename: string): Promise<void> {
  const { data, headers } = await apiClient.get<Blob>(
    `/api/v1/job-requirements/${jobRequirementId}/submissions/download-all`,
    { responseType: 'blob' },
  )
  const disposition = headers['content-disposition'] ?? ''
  const match = /filename="?([^"]+)"?/.exec(disposition)
  const resolvedFilename = match?.[1] ?? filename

  const url = URL.createObjectURL(
    new Blob([data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = resolvedFilename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function downloadApprovedClientSubmissions(
  clientId: string,
  filename: string,
): Promise<void> {
  const { data, headers } = await apiClient.get<Blob>(
    `/api/v1/submissions/owner/download-approved/${clientId}`,
    { responseType: 'blob' },
  )
  const disposition = headers['content-disposition'] ?? ''
  const match = /filename="?([^"]+)"?/.exec(disposition)
  const resolvedFilename = match?.[1] ?? filename

  const url = URL.createObjectURL(
    new Blob([data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = resolvedFilename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function fetchOwnerDashboard(): Promise<OwnerDashboardClient[]> {
  const { data } = await apiClient.get<OwnerDashboardClient[]>('/api/v1/submissions/owner/dashboard')
  return data
}
