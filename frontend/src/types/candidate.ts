export interface Skill {
  id?: string
  name: string
  years_experience?: number | null
  proficiency_level?: string | null
}

export interface Education {
  id?: string
  degree: string
  specialization?: string | null
  institution?: string | null
  start_year?: number | null
  end_year?: number | null
  percentage?: number | null
}

export interface WorkExperience {
  id?: string
  company_name: string
  designation?: string | null
  start_date?: string | null
  end_date?: string | null
  currently_working?: boolean
  job_description?: string | null
}

export interface Candidate {
  id: string
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
  uae_experience_years?: number | null
  industry?: string | null
  current_company?: string | null
  current_designation?: string | null
  current_ctc?: number | null
  expected_ctc?: number | null
  notice_period?: string | null
  resume_url?: string | null
  candidate_status: string
  source?: string | null
  created_by?: string | null
  created_at?: string | null
  updated_at?: string | null
  skills: Skill[]
  education_records: Education[]
  work_experiences: WorkExperience[]
}

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
  uae_experience_years?: number | null
  industry?: string | null
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

export interface CandidateUpdatePayload {
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
  uae_experience_years?: number | null
  industry?: string | null
  current_company?: string | null
  current_designation?: string | null
  current_ctc?: number | null
  expected_ctc?: number | null
  notice_period?: string | null
  resume_url?: string | null
  candidate_status: string
  source?: string | null
  created_by?: string | null
  skills: SkillDraft[]
  education_records: EducationDraft[]
  work_experiences: WorkExperienceDraft[]
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

export function candidateToDraft(candidate: Candidate): CandidateDraft {
  return {
    first_name: candidate.first_name,
    last_name: candidate.last_name,
    email: candidate.email,
    nationality: candidate.nationality,
    date_of_birth: candidate.date_of_birth,
    languages_known: candidate.languages_known,
    phone: candidate.phone,
    visa_status: candidate.visa_status,
    linkedin_url: candidate.linkedin_url,
    current_location: candidate.current_location,
    preferred_location: candidate.preferred_location,
    total_experience_years: candidate.total_experience_years,
    uae_experience_years: candidate.uae_experience_years,
    industry: candidate.industry,
    current_company: candidate.current_company,
    current_designation: candidate.current_designation,
    current_ctc: candidate.current_ctc,
    expected_ctc: candidate.expected_ctc,
    notice_period: candidate.notice_period,
    resume_url: candidate.resume_url ?? '',
    source: candidate.source,
    candidate_status: candidate.candidate_status,
    skills: candidate.skills.map((s) => ({
      name: s.name,
      years_experience: s.years_experience,
      proficiency_level: s.proficiency_level,
    })),
    education: candidate.education_records.map((e) => ({
      degree: e.degree,
      specialization: e.specialization,
      institution: e.institution,
      start_year: e.start_year,
      end_year: e.end_year,
      percentage: e.percentage,
    })),
    work_experience: candidate.work_experiences.map((w) => ({
      company_name: w.company_name,
      designation: w.designation,
      start_date: w.start_date,
      end_date: w.end_date,
      currently_working: w.currently_working ?? false,
      job_description: w.job_description,
    })),
  }
}

export function draftToUpdatePayload(draft: CandidateDraft, createdBy?: string | null): CandidateUpdatePayload {
  return {
    first_name: draft.first_name,
    last_name: draft.last_name,
    email: draft.email,
    nationality: draft.nationality,
    date_of_birth: draft.date_of_birth,
    languages_known: draft.languages_known,
    phone: draft.phone,
    visa_status: draft.visa_status,
    linkedin_url: draft.linkedin_url,
    current_location: draft.current_location,
    preferred_location: draft.preferred_location,
    total_experience_years: draft.total_experience_years,
    uae_experience_years: draft.uae_experience_years,
    industry: draft.industry,
    current_company: draft.current_company,
    current_designation: draft.current_designation,
    current_ctc: draft.current_ctc,
    expected_ctc: draft.expected_ctc,
    notice_period: draft.notice_period,
    resume_url: draft.resume_url,
    candidate_status: draft.candidate_status ?? 'active',
    source: draft.source,
    created_by: createdBy,
    skills: draft.skills,
    education_records: draft.education,
    work_experiences: draft.work_experience,
  }
}
