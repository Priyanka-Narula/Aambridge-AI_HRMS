export type UserRole = 'owner' | 'recruiter'

export interface RecruiterProfile {
  id: string
  employee_code: string
  designation?: string | null
  team?: string | null
  status: string
}

export interface AuthUser {
  id: string
  first_name: string
  last_name: string
  email: string
  phone?: string | null
  location?: string | null
  languages_spoken?: string | null
  status: string
  role: UserRole
  recruiter?: RecruiterProfile | null
  created_at?: string | null
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface DateRange {
  start: string
  end: string
}

export interface RecruiterListItem {
  id: string
  first_name: string
  last_name: string
  email: string
  phone?: string | null
  status: string
  role: UserRole
  recruiter?: RecruiterProfile | null
  created_at?: string | null
}

export interface RecruiterCreatePayload {
  first_name: string
  last_name: string
  email: string
  password: string
  phone?: string | null
  location?: string | null
  languages_spoken?: string | null
  employee_code: string
  designation?: string | null
  team?: string | null
  joining_date?: string | null
}
