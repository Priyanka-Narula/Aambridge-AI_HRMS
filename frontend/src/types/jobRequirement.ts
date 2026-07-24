export type JobRequirementStatus = 'open' | 'on_hold' | 'closed' | 'filled'
export type OwnerStatusType = 'pending_review' | 'approved' | 'rejected'

export interface SubmissionField {
  field: string
  type: string
  required: boolean
}

export interface CandidateSubmission {
  id: string
  candidate_id: string
  candidate_name: string
  candidate_email: string
  job_requirement_id: string
  job_title: string
  client_id: string
  client_name: string
  submitted_by_id: string | null
  submitted_by_name: string | null
  submitted_at: string | null
  current_stage: string | null
  status: string
  owner_status: OwnerStatusType
  in_pipeline?: boolean
  submission_data: Record<string, string> | null
}

export interface OwnerDashboardJob {
  job_requirement_id: string
  job_title: string
  status: string
  open_positions: number | null
  submissions: CandidateSubmission[]
}

export interface OwnerDashboardClient {
  client_id: string
  company_name: string
  jobs: OwnerDashboardJob[]
}

export interface JobRequirementListItem {
  id: string
  client_id: string
  client_name: string
  assigned_to: string | null
  assigned_recruiter_name: string | null
  job_title: string
  department?: string | null
  employment_type?: string | null
  work_mode?: string | null
  experience_min?: number | null
  experience_max?: number | null
  salary_min?: number | null
  salary_max?: number | null
  open_positions?: number | null
  job_description?: string | null
  location?: string | null
  priority?: string | null
  status: JobRequirementStatus | string
  requirement_type?: string | null
  created_by: string
  created_at?: string | null
  client_submission_format?: SubmissionField[] | null
}

export interface JobRequirementCreatePayload {
  client_id: string
  assigned_to: string
  job_title: string
  department?: string | null
  employment_type?: string | null
  work_mode?: string | null
  experience_min?: number | null
  experience_max?: number | null
  salary_min?: number | null
  salary_max?: number | null
  open_positions?: number | null
  job_description?: string | null
  location?: string | null
  priority?: string | null
  requirement_type?: string | null
  status?: JobRequirementStatus
}

export type JobRequirementUpdatePayload = Partial<JobRequirementCreatePayload>
