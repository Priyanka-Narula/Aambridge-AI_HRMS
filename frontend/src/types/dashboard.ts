import type {
  BusinessTrend,
  ExecutiveKpi,
  HiringFunnel,
  OpenJobRow,
  RecruiterLeaderboardRow,
} from '@/types/commandCenter'

export type DashboardRole = 'owner' | 'recruiter'

export interface NamedCount {
  label: string
  value: number
}

export interface PipelineStageStat {
  name: string
  count: number
  order_no: number
}

export interface HeatmapCell {
  dow: number
  hour: number
  value: number
}

export interface DashboardKpis {
  total_candidates: number
  active_candidates: number
  inactive_candidates: number
  pending_approval: number
  approved_candidates: number
  rejected_candidates: number
  submissions_pending: number
  submissions_approved: number
  submissions_rejected: number
  total_recruiters: number
  active_recruiters: number
  total_clients: number
  open_jobs: number
  closed_jobs: number
  placements: number
  monthly_placements: number
  revenue: number
  average_time_to_hire_days: number | null
  in_pipeline: number
  my_candidates: number
  approved: number
  rejected: number
  interviews_scheduled: number
  offers: number
  clients_assigned: number
  jobs_assigned: number
}

export interface DashboardCharts {
  pipeline_stages: PipelineStageStat[]
  candidate_status: NamedCount[]
  recruiter_performance: NamedCount[]
  client_placements: NamedCount[]
  recruiter_activity_heatmap: HeatmapCell[]
  candidate_uploads_monthly: NamedCount[]
  placements_monthly: NamedCount[]
  interviews_vs_offers: NamedCount[]
}

export interface DashboardTables {
  recent_placements: Array<Record<string, unknown>>
  recent_activities: Array<Record<string, unknown>>
  notifications: Array<Record<string, unknown>>
  recent_candidates: Array<Record<string, unknown>>
  pending_tasks: Array<Record<string, unknown>>
  todays_interviews: Array<Record<string, unknown>>
  upcoming_interviews: Array<Record<string, unknown>>
  recent_feedback: Array<Record<string, unknown>>
}

export interface AnalyticsDashboard {
  role: DashboardRole
  kpis: DashboardKpis
  charts: DashboardCharts
  tables: DashboardTables
}

/** Legacy compact stats */
export interface DashboardStats {
  open_jobs: number
  closed_jobs: number
  active_candidates: number
  submissions_total: number
  submissions_pending: number
  submissions_approved: number
  in_pipeline: number
  interviews_scheduled: number
  offers_pending: number
  joined: number
  pipeline_stages: PipelineStageStat[]
}

export interface DashboardWsEvent {
  type: string
  widgets?: string[]
  detail?: Record<string, unknown>
}

export interface DashboardNotification {
  id: string
  type: string
  title: string
  description: string
  created_at: string | null
  actor?: string | null
}

export interface DashboardNotificationsResponse {
  items: DashboardNotification[]
  unread_count: number
}

export interface RecruiterMetrics {
  recruiter_id: string
  name: string
  positions_closed_this_month: number
  positions_closed_total: number
  submissions_total: number
  interviews_total: number
  offers_total: number
  conversion_rate: number
  avg_time_to_hire_days: number | null
  approved_submissions: number
  accepted_offers: number
  submission_quality: number
  offer_acceptance_rate: number
  avg_response_days: number | null
  productivity_score: number
  score_breakdown: RecruiterScoreBreakdown
  placements_monthly: NamedCount[]
}

export interface RecruiterScoreBreakdown {
  placements: number
  interviews: number
  submission_quality: number
  offer_acceptance: number
  response_time: number
}

export type RecruiterPerformancePeriod = 'monthly' | 'till_date'

export interface RecruiterPerformanceResponse {
  recruiters: RecruiterMetrics[]
  industries: string[]
}

export interface RecruiterFocusItem {
  key: string
  label: string
  value: number
  tone: 'neutral' | 'attention' | 'urgent' | 'positive'
  action_href: string
}

export interface RecruiterActionItem {
  key: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  count: number
  action_label: string
  action_href: string
}

export interface RecruiterStanding {
  rank: number | null
  total_recruiters: number
  team_median_score: number
  me: RecruiterLeaderboardRow | null
  peers: RecruiterLeaderboardRow[]
}

export interface RecruiterCommandData {
  today_focus: RecruiterFocusItem[]
  kpis: ExecutiveKpi[]
  standing: RecruiterStanding
  hiring_funnel: HiringFunnel
  action_queue: RecruiterActionItem[]
  job_health: OpenJobRow[]
  personal_trend: BusinessTrend
}
