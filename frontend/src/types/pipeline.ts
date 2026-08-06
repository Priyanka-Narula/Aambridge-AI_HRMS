export interface PipelineStage {
  id: string
  name: string
  order_no: number
}

export interface InterviewRound {
  id: string
  interview_round: number
  status: string
  scheduled_datetime: string | null
  mode: string | null
  interviewer_name: string | null
}

export interface PipelineCard {
  id: string
  candidate_id: string
  candidate_name: string
  candidate_email: string
  candidate_phone: string | null
  current_designation: string | null
  current_company: string | null
  total_experience_years: number | null
  job_requirement_id: string
  job_title: string
  client_id: string
  client_name: string
  assigned_recruiter_id: string | null
  assigned_recruiter_name: string | null
  job_assignee_user_id: string | null
  job_assignee_name: string | null
  current_stage_id: string | null
  current_stage: string | null
  status: string
  owner_status: string
  applied_date: string | null
  submitted_at: string | null
  remarks: string | null
  interview_round: number | null
  interview_scheduled_at: string | null
  interview_mode: string | null
  interview_status: string | null
  interviewer_name: string | null
  interviews: InterviewRound[]
  offer_ctc: number | null
  offer_date: string | null
  offer_status: string | null
  offer_joining_date: string | null
  joined_date: string | null
}

export interface PipelineBoard {
  stages: PipelineStage[]
  cards: PipelineCard[]
}

export interface StageHistoryItem {
  id: string
  stage_id: string
  stage_name: string
  moved_by: string
  moved_by_name: string | null
  remarks: string | null
  created_at: string
}

export interface CandidateApplicationHistory {
  application_id: string
  job_requirement_id: string
  job_title: string
  client_id: string
  client_name: string
  current_stage: string | null
  owner_status: string
  status: string
  submitted_at: string | null
  history: StageHistoryItem[]
}

export interface CandidateStageHistory {
  candidate_id: string
  applications: CandidateApplicationHistory[]
}

export interface PipelineMovePayload {
  stage_name: string
  remarks?: string | null
  offered_ctc?: number | null
  joining_date?: string | null
  joined_date?: string | null
  revenue_generated?: number | null
  interview_scheduled_at?: string | null
  interviewer_name?: string | null
  interview_mode?: string | null
}

export type InterviewAction = 'cancel' | 'change_date' | 'no_show' | 'reschedule'

export interface InterviewActionPayload {
  action: InterviewAction
  interview_scheduled_at?: string | null
  interviewer_name?: string | null
  interview_mode?: string | null
  remarks?: string | null
}

export interface ShareApprovedPayload {
  to_emails?: string[]
  subject?: string
  message?: string
  application_ids?: string[]
}

export interface ShareApprovedResult {
  sent_to: string[]
  subject: string
  attachment: string | null
  candidate_count: number
}

/** Main hiring path; stage moves mirror the backend's immediate-next rules. */
export const FORWARD_ORDER = [
  'Applied',
  'Shortlisted',
  'Interview',
  'Offer',
  'Joined',
] as const

export function nextForwardStage(currentStage: string): string | null {
  const index = FORWARD_ORDER.indexOf(currentStage as (typeof FORWARD_ORDER)[number])
  return index >= 0 ? (FORWARD_ORDER[index + 1] ?? null) : null
}

export function resumeStageFromHistory(history: StageHistoryItem[]): string | null {
  for (const item of [...history].reverse()) {
    if (FORWARD_ORDER.includes(item.stage_name as (typeof FORWARD_ORDER)[number])) {
      return item.stage_name
    }
  }
  return null
}

export function allowedStageTargets(currentStage: string, resumeStage?: string | null): string[] {
  if (currentStage === 'Joined' || currentStage === 'Rejected') return []
  if (currentStage === 'On Hold') {
    return [...(resumeStage ? [resumeStage] : []), 'Rejected']
  }
  if (currentStage === 'Interview') {
    return ['Interview', 'Offer', 'On Hold', 'Rejected']
  }
  const nextStage = nextForwardStage(currentStage)
  return [...(nextStage ? [nextStage] : []), 'On Hold', 'Rejected']
}

/** @deprecated use allowedStageTargets */
export const PIPELINE_TRANSITIONS: Record<string, string[]> = {
  Applied: allowedStageTargets('Applied'),
  Shortlisted: allowedStageTargets('Shortlisted'),
  Interview: allowedStageTargets('Interview'),
  Offer: allowedStageTargets('Offer'),
  Joined: [],
  'On Hold': allowedStageTargets('On Hold'),
  Rejected: [],
}
