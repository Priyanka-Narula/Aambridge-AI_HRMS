export type TrendGrain = 'weekly' | 'monthly' | 'quarterly' | 'yearly'
export type WorkloadLevel = 'light' | 'balanced' | 'heavy' | 'overloaded'
export type ClientBadge = 'Healthy' | 'Needs Attention' | 'Inactive'
export type JobHealthStatus = 'healthy' | 'urgent' | 'overdue' | 'frozen'
export type AlertSeverity = 'amber' | 'red'

export interface SparkPoint {
  label: string
  value: number
}

export interface ExecutiveKpi {
  key: string
  label: string
  value: number | null
  unit: 'number' | 'percent' | 'days'
  delta_pct: number | null
  trend: 'up' | 'down' | 'flat'
  sparkline: SparkPoint[]
  tooltip: string
}

export interface TrendSeries {
  key: string
  label: string
  color: string
  points: SparkPoint[]
}

export interface BusinessTrend {
  grain: TrendGrain
  series: TrendSeries[]
}

export interface FunnelStage {
  name: string
  count: number
  conversion_pct: number | null
  dropoff_pct: number | null
  is_highest_dropoff: boolean
}

export interface HiringFunnel {
  stages: FunnelStage[]
  insight: string
}

export interface RecruiterLeaderboardRow {
  recruiter_id: string
  user_id: string
  name: string
  initials: string
  placements: number
  active_candidates: number
  interviews_scheduled: number
  avg_time_to_hire_days: number | null
  offer_acceptance_rate: number | null
  assigned_jobs: number
  workload_level: WorkloadLevel
  productivity_score: number
}

export interface WorkloadBar {
  recruiter_id: string
  name: string
  assigned_jobs: number
  overloaded: boolean
}

export interface ClientHealthCard {
  client_id: string
  name: string
  status_badge: ClientBadge
  open_positions: number
  placements: number
  candidates_in_pipeline: number
  avg_hiring_time_days: number | null
  jobs_pending_too_long: number
  last_activity: string | null
  client_status: string
}

export interface JobHealthCounts {
  healthy: number
  urgent: number
  overdue: number
  frozen: number
}

export interface OpenJobRow {
  job_id: string
  job_title: string
  client_name: string
  recruiter_name: string | null
  days_open: number
  candidates: number
  current_stage: string | null
  status: JobHealthStatus
  exceeds_sla: boolean
}

export interface PipelineMetricCard {
  key: string
  label: string
  value: number
  delta: number | null
  delta_label?: string
}

export interface ActivityItem {
  id: string
  time: string | null
  actor: string | null
  title: string
  description: string
  type: string
}

export interface AlertItem {
  id: string
  severity: AlertSeverity
  title: string
  description: string
  count: number
  action_label: string
  action_href: string
}

export interface FilterOptions {
  recruiters: Array<{ id: string; name: string }>
  clients: Array<{ id: string; name: string }>
  departments: string[]
  locations: string[]
  job_statuses: string[]
}

export interface CommandCenterFilters {
  start?: string
  end?: string
  trend_grain?: TrendGrain
  recruiter_id?: string
  client_id?: string
  department?: string
  job_status?: string
  location?: string
  activity_limit?: number
}

export interface CommandCenterData {
  kpis: ExecutiveKpi[]
  business_trend: BusinessTrend
  hiring_funnel: HiringFunnel
  recruiter_leaderboard: RecruiterLeaderboardRow[]
  recruiter_workload: WorkloadBar[]
  workload_insight: string
  client_health: ClientHealthCard[]
  job_health_counts: JobHealthCounts
  open_jobs: OpenJobRow[]
  pipeline_summary: PipelineMetricCard[]
  activity_feed: ActivityItem[]
  alerts: AlertItem[]
  filter_options: FilterOptions
}
