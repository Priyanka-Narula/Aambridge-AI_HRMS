import apiClient from '@/api/client'
import type {
  Candidate,
  CandidateApprovalResponse,
  CandidateDraft,
  CandidateUpdatePayload,
  CvUploadResponse,
} from '@/types/candidate'

export async function fetchCandidates(): Promise<Candidate[]> {
  const { data } = await apiClient.get<Candidate[]>('/api/v1/candidates/')
  return data
}

export async function fetchCandidate(id: string): Promise<Candidate> {
  const { data } = await apiClient.get<Candidate>(`/api/v1/candidates/${id}`)
  return data
}

export async function updateCandidate(id: string, payload: CandidateUpdatePayload): Promise<Candidate> {
  const { data } = await apiClient.put<Candidate>(`/api/v1/candidates/${id}`, payload)
  return data
}

export async function deleteCandidate(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/candidates/${id}`)
}

export async function uploadCv(
  file: File,
  createdBy: string,
): Promise<CvUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await apiClient.post<CvUploadResponse>(
    '/api/v1/candidates/upload',
    formData,
    {
      params: { auto_approve: false, created_by: createdBy },
      headers: { 'Content-Type': 'multipart/form-data' },
    },
  )
  return data
}

export async function approveCandidate(
  candidate: CandidateDraft,
  createdBy: string,
): Promise<CandidateApprovalResponse> {
  const { data } = await apiClient.post<CandidateApprovalResponse>(
    '/api/v1/candidates/approve',
    {
      candidate: { ...candidate, candidate_status: 'active' },
      created_by: createdBy,
    },
  )
  return data
}
