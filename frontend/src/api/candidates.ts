import apiClient from '@/api/client'
import type {
  CandidateApprovalResponse,
  CandidateDraft,
  CvUploadResponse,
} from '@/types/candidate'

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
