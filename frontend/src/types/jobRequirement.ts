export type JobRequirementStatus = 'open' | 'on_hold' | 'closed' | 'filled'

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
