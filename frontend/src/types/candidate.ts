export interface SkillDraft {
  name: string
  years_experience?: number | null
  proficiency_level?: string | null
}

export interface EducationDraft {
  degree: string
  specialization?: string | null
  institution?: string | null
  start_year?: number | null
  end_year?: number | null
  percentage?: number | null
}

export interface WorkExperienceDraft {
  company_name: string
  designation?: string | null
  start_date?: string | null
  end_date?: string | null
  currently_working?: boolean
  job_description?: string | null
}

export interface CandidateDraft {
  first_name: string
  last_name: string
  email: string
  nationality?: string | null
  date_of_birth?: string | null
  languages_known?: string | null
  phone?: string | null
  visa_status?: string | null
  linkedin_url?: string | null
  current_location?: string | null
  preferred_location?: string | null
  total_experience_years?: number | null
  current_company?: string | null
  current_designation?: string | null
  current_ctc?: number | null
  expected_ctc?: number | null
  notice_period?: string | null
  resume_url: string
  source?: string | null
  candidate_status?: string
  skills: SkillDraft[]
  education: EducationDraft[]
  work_experience: WorkExperienceDraft[]
}

export interface CvUploadResponse {
  filename: string
  status: string
  parsing_method?: string
  total_characters: number
  text_preview: string
  bucket: string
  object_key: string
  storage_uri: string
  candidate_preview: CandidateDraft
  validation_errors: string[]
  saved_candidate_id?: string
  message?: string
}

export interface CandidateApprovalResponse {
  status: string
  candidate_id: string
  email: string
  candidate_status: string
}
