import type { UserRole } from './auth'

export type NavIconName =
  | 'dashboard'
  | 'users'
  | 'employees'
  | 'recruitment'
  | 'pipeline'
  | 'candidates'
  | 'interviews'
  | 'team'
  | 'approvals'
  | 'reports'
  | 'organizations'
  | 'settings'
  | 'job-postings'

export interface NavItem {
  id: string
  label: string
  icon: NavIconName
  route: string
  roles: UserRole[]
}
