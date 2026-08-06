import apiClient from '@/api/client'
import type {
  CandidateStageHistory,
  InterviewActionPayload,
  PipelineBoard,
  PipelineCard,
  PipelineMovePayload,
  ShareApprovedPayload,
  ShareApprovedResult,
  StageHistoryItem,
} from '@/types/pipeline'

export async function fetchPipelineBoard(params?: {
  client_id?: string
  job_requirement_id?: string
  search?: string
}): Promise<PipelineBoard> {
  const { data } = await apiClient.get<PipelineBoard>('/api/v1/pipeline/board', { params })
  return data
}

export async function shortlistApplications(
  applicationIds: string[],
  remarks?: string,
): Promise<PipelineCard[]> {
  const { data } = await apiClient.post<PipelineCard[]>('/api/v1/pipeline/shortlist', {
    application_ids: applicationIds,
    remarks,
  })
  return data
}

export async function movePipelineStage(
  appId: string,
  payload: PipelineMovePayload,
): Promise<PipelineCard> {
  const { data } = await apiClient.patch<PipelineCard>(
    `/api/v1/pipeline/applications/${appId}/stage`,
    payload,
  )
  return data
}

export async function updatePipelineInterview(
  appId: string,
  payload: InterviewActionPayload,
): Promise<PipelineCard> {
  const { data } = await apiClient.patch<PipelineCard>(
    `/api/v1/pipeline/applications/${appId}/interview`,
    payload,
  )
  return data
}

export async function fetchPipelineHistory(appId: string): Promise<StageHistoryItem[]> {
  const { data } = await apiClient.get<StageHistoryItem[]>(
    `/api/v1/pipeline/applications/${appId}/history`,
  )
  return data
}

export async function fetchCandidateStageHistory(
  candidateId: string,
): Promise<CandidateStageHistory> {
  const { data } = await apiClient.get<CandidateStageHistory>(
    `/api/v1/pipeline/candidates/${candidateId}/history`,
  )
  return data
}

export async function fetchEmailStatus(): Promise<{ configured: boolean }> {
  const { data } = await apiClient.get<{ configured: boolean }>('/api/v1/pipeline/email-status')
  return data
}

export async function shareApprovedProfiles(
  clientId: string,
  payload: ShareApprovedPayload = {},
): Promise<ShareApprovedResult> {
  const { data } = await apiClient.post<ShareApprovedResult>(
    `/api/v1/pipeline/share-approved/${clientId}`,
    payload,
  )
  return data
}
