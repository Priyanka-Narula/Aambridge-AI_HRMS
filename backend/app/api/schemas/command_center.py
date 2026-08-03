from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SparkPoint(BaseModel):
    label: str
    value: float


class ExecutiveKpi(BaseModel):
    key: str
    label: str
    value: float | None = None
    unit: Literal["number", "percent", "days"] = "number"
    delta_pct: float | None = None
    trend: Literal["up", "down", "flat"] = "flat"
    sparkline: list[SparkPoint] = Field(default_factory=list)
    tooltip: str = ""


class TrendSeries(BaseModel):
    key: str
    label: str
    color: str
    points: list[SparkPoint] = Field(default_factory=list)


class BusinessTrend(BaseModel):
    grain: Literal["weekly", "monthly", "quarterly", "yearly"]
    series: list[TrendSeries] = Field(default_factory=list)


class FunnelStage(BaseModel):
    name: str
    count: int
    conversion_pct: float | None = None
    dropoff_pct: float | None = None
    is_highest_dropoff: bool = False


class HiringFunnel(BaseModel):
    stages: list[FunnelStage] = Field(default_factory=list)
    insight: str = ""


class RecruiterLeaderboardRow(BaseModel):
    recruiter_id: str
    user_id: str
    name: str
    initials: str
    placements: int = 0
    active_candidates: int = 0
    interviews_scheduled: int = 0
    avg_time_to_hire_days: float | None = None
    offer_acceptance_rate: float | None = None
    assigned_jobs: int = 0
    workload_level: Literal["light", "balanced", "heavy", "overloaded"] = "balanced"
    productivity_score: float = 0


class WorkloadBar(BaseModel):
    recruiter_id: str
    name: str
    assigned_jobs: int = 0
    overloaded: bool = False


class ClientHealthCard(BaseModel):
    client_id: str
    name: str
    status_badge: Literal["Healthy", "Needs Attention", "Inactive"]
    open_positions: int = 0
    placements: int = 0
    candidates_in_pipeline: int = 0
    avg_hiring_time_days: float | None = None
    jobs_pending_too_long: int = 0
    last_activity: str | None = None
    client_status: str = "active"


class JobHealthCounts(BaseModel):
    healthy: int = 0
    urgent: int = 0
    overdue: int = 0
    frozen: int = 0


class OpenJobRow(BaseModel):
    job_id: str
    job_title: str
    client_name: str
    recruiter_name: str | None = None
    days_open: int = 0
    candidates: int = 0
    current_stage: str | None = None
    status: Literal["healthy", "urgent", "overdue", "frozen"]
    exceeds_sla: bool = False


class PipelineMetricCard(BaseModel):
    key: str
    label: str
    value: int
    delta: int | None = None
    delta_label: str = "vs yesterday"


class ActivityItem(BaseModel):
    id: str
    time: str | None = None
    actor: str | None = None
    title: str
    description: str
    type: str = "activity"


class AlertItem(BaseModel):
    id: str
    severity: Literal["amber", "red"]
    title: str
    description: str
    count: int = 0
    action_label: str
    action_href: str


class FilterOptions(BaseModel):
    recruiters: list[dict[str, str]] = Field(default_factory=list)
    clients: list[dict[str, str]] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    job_statuses: list[str] = Field(default_factory=list)


class CommandCenterResponse(BaseModel):
    kpis: list[ExecutiveKpi] = Field(default_factory=list)
    business_trend: BusinessTrend
    hiring_funnel: HiringFunnel
    recruiter_leaderboard: list[RecruiterLeaderboardRow] = Field(default_factory=list)
    recruiter_workload: list[WorkloadBar] = Field(default_factory=list)
    workload_insight: str = ""
    client_health: list[ClientHealthCard] = Field(default_factory=list)
    job_health_counts: JobHealthCounts
    open_jobs: list[OpenJobRow] = Field(default_factory=list)
    pipeline_summary: list[PipelineMetricCard] = Field(default_factory=list)
    activity_feed: list[ActivityItem] = Field(default_factory=list)
    alerts: list[AlertItem] = Field(default_factory=list)
    filter_options: FilterOptions
