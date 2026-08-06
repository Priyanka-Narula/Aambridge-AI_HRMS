from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class NamedCount(BaseModel):
    label: str
    value: int


class PipelineStageStat(BaseModel):
    name: str
    count: int
    order_no: int


class HeatmapCell(BaseModel):
    dow: int
    hour: int
    value: int


class DashboardKpis(BaseModel):
    total_candidates: int = 0
    active_candidates: int = 0
    inactive_candidates: int = 0
    pending_approval: int = 0
    approved_candidates: int = 0
    rejected_candidates: int = 0
    submissions_pending: int = 0
    submissions_approved: int = 0
    submissions_rejected: int = 0
    total_recruiters: int = 0
    active_recruiters: int = 0
    total_clients: int = 0
    open_jobs: int = 0
    closed_jobs: int = 0
    placements: int = 0
    monthly_placements: int = 0
    revenue: float = 0
    average_time_to_hire_days: float | None = None
    in_pipeline: int = 0
    # Recruiter-focused aliases
    my_candidates: int = 0
    approved: int = 0
    rejected: int = 0
    interviews_scheduled: int = 0
    offers: int = 0
    clients_assigned: int = 0
    jobs_assigned: int = 0


class DashboardCharts(BaseModel):
    pipeline_stages: list[PipelineStageStat] = Field(default_factory=list)
    candidate_status: list[NamedCount] = Field(default_factory=list)
    recruiter_performance: list[NamedCount] = Field(default_factory=list)
    client_placements: list[NamedCount] = Field(default_factory=list)
    recruiter_activity_heatmap: list[HeatmapCell] = Field(default_factory=list)
    candidate_uploads_monthly: list[NamedCount] = Field(default_factory=list)
    placements_monthly: list[NamedCount] = Field(default_factory=list)
    interviews_vs_offers: list[NamedCount] = Field(default_factory=list)


class DashboardTables(BaseModel):
    recent_placements: list[dict[str, Any]] = Field(default_factory=list)
    recent_activities: list[dict[str, Any]] = Field(default_factory=list)
    notifications: list[dict[str, Any]] = Field(default_factory=list)
    recent_candidates: list[dict[str, Any]] = Field(default_factory=list)
    pending_tasks: list[dict[str, Any]] = Field(default_factory=list)
    todays_interviews: list[dict[str, Any]] = Field(default_factory=list)
    upcoming_interviews: list[dict[str, Any]] = Field(default_factory=list)
    recent_feedback: list[dict[str, Any]] = Field(default_factory=list)


class DashboardNotificationItem(BaseModel):
    id: str
    type: str
    title: str
    description: str
    created_at: str | None = None
    actor: str | None = None


class DashboardNotificationsResponse(BaseModel):
    items: list[DashboardNotificationItem] = Field(default_factory=list)
    unread_count: int = 0


class RecruiterScoreBreakdown(BaseModel):
    placements: float = 0
    interviews: float = 0
    submission_quality: float = 0
    offer_acceptance: float = 0
    response_time: float = 0


class RecruiterMetrics(BaseModel):
    recruiter_id: str
    name: str
    positions_closed_this_month: int = 0
    positions_closed_total: int = 0
    submissions_total: int = 0
    interviews_total: int = 0
    offers_total: int = 0
    conversion_rate: float = 0
    avg_time_to_hire_days: float | None = None
    approved_submissions: int = 0
    accepted_offers: int = 0
    submission_quality: float = 0
    offer_acceptance_rate: float = 0
    avg_response_days: float | None = None
    productivity_score: float = 0
    score_breakdown: RecruiterScoreBreakdown = Field(default_factory=RecruiterScoreBreakdown)
    placements_monthly: list[NamedCount] = Field(default_factory=list)


class RecruiterPerformanceResponse(BaseModel):
    recruiters: list[RecruiterMetrics] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)


class AnalyticsDashboardResponse(BaseModel):
    role: Literal["owner", "recruiter"]
    kpis: DashboardKpis
    charts: DashboardCharts
    tables: DashboardTables


# Legacy shape kept for older clients during transition
class DashboardStatsResponse(BaseModel):
    open_jobs: int = 0
    closed_jobs: int = 0
    active_candidates: int = 0
    submissions_total: int = 0
    submissions_pending: int = 0
    submissions_approved: int = 0
    in_pipeline: int = 0
    interviews_scheduled: int = 0
    offers_pending: int = 0
    joined: int = 0
    pipeline_stages: list[PipelineStageStat] = Field(default_factory=list)
