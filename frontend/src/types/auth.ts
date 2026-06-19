export type UserRole = 'admin' | 'recruiter' | 'manager' | 'client'

export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  avatarInitials: string
}

export interface DateRange {
  start: string
  end: string
}
