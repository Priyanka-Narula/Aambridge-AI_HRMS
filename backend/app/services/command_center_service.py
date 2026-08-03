"""Database-backed aggregates for the owner command center.

Every response section is assembled on request from PostgreSQL: KPIs use
``job_requirements``, ``clients``, applications, offers, and placements;
trends and funnel use applications, stages, interviews, offers, and
placements; recruiter panels use recruiters/users plus those hiring tables;
client/job panels use clients, jobs, applications, and activities; operational
panels use candidates, interviews, offers, stage history, and attendance.
The owner dashboard performs a full refetch on filter/date changes and owner
dashboard WebSocket events. No section is scheduled, seeded, or synthesized.

Rule-based fields are intentionally derived from those query results:
``SLA_DAYS`` (45), ``URGENT_DAYS`` (30), ``PENDING_TOO_LONG_DAYS`` (45), and
``OVERLOAD_RATIO`` (1.5) determine job/client/workload states; productivity is
a weighted within-result min/max score; funnel ratios are snapshot stage
ratios, not historical cohort conversion.
"""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import cast, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.types import Date

from app.core.config import settings
from app.core.security import ROLE_OWNER, normalize_role
from app.models.attendance import AttendanceRecord
from app.models.candidate import Candidate
from app.models.job_requirement import JobRequirement
from app.models.offer import Offer, Placement
from app.models.pipeline import (
    ApplicationStageHistory,
    CandidateApplication,
    Interview,
    PipelineStage,
)
from app.models.user_access import Client, ClientActivity, Recruiter, User
from app.services.pipeline_service import BOARD_STAGE_NAMES

SLA_DAYS = 45
URGENT_DAYS = 30
PENDING_TOO_LONG_DAYS = 45
OVERLOAD_RATIO = 1.5

FUNNEL_STAGES = ["Applied", "Shortlisted", "Interview", "Offer", "Joined"]
OFFICE_TZ = ZoneInfo(settings.OFFICE_TIMEZONE or "Asia/Dubai")


def get_command_center(
    db: Session,
    current_user: User,
    *,
    start: date | None = None,
    end: date | None = None,
    trend_grain: Literal["weekly", "monthly", "quarterly", "yearly"] = "monthly",
    recruiter_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
    department: str | None = None,
    job_status: str | None = None,
    location: str | None = None,
    activity_limit: int = 5,
) -> dict:
    if normalize_role(current_user.role.name) != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")

    today = datetime.now(OFFICE_TZ).date()
    end = end or today
    start = start or (end - timedelta(days=30))
    filters = _FilterContext(
        start=start,
        end=end,
        today=today,
        recruiter_user_id=_recruiter_user_id(db, recruiter_id) if recruiter_id else None,
        client_id=client_id,
        department=department.strip() if department else None,
        job_status=job_status.strip() if job_status else None,
        location=location.strip() if location else None,
    )

    open_jobs = _open_job_rows(db, filters)
    leaderboard = _recruiter_leaderboard(db, filters)
    workload = _recruiter_workload(db, filters, leaderboard)
    clients = _client_health(db, filters)
    funnel = _hiring_funnel(db, filters)
    kpis = _executive_kpis(db, filters, leaderboard)
    trend = _business_trend(db, filters, grain=trend_grain)
    pipeline = _pipeline_summary(db, filters)
    activity = _activity_feed(db, filters, limit=activity_limit)
    alerts = _alerts(db, filters, open_jobs, leaderboard)

    return {
        "kpis": kpis,
        "business_trend": trend,
        "hiring_funnel": funnel,
        "recruiter_leaderboard": leaderboard,
        "recruiter_workload": workload["bars"],
        "workload_insight": workload["insight"],
        "client_health": clients,
        "job_health_counts": _job_health_counts(open_jobs),
        "open_jobs": open_jobs[:40],
        "pipeline_summary": pipeline,
        "activity_feed": activity,
        "alerts": alerts,
        "filter_options": _filter_options(db),
    }


class _FilterContext:
    def __init__(
        self,
        *,
        start: date,
        end: date,
        today: date,
        recruiter_user_id: uuid.UUID | None,
        client_id: uuid.UUID | None,
        department: str | None,
        job_status: str | None,
        location: str | None,
    ):
        self.start = start
        self.end = end
        self.today = today
        self.recruiter_user_id = recruiter_user_id
        self.client_id = client_id
        self.department = department
        self.job_status = job_status
        self.location = location
        self.start_dt = datetime.combine(start, datetime.min.time(), tzinfo=OFFICE_TZ)
        self.end_dt = datetime.combine(end, datetime.max.time(), tzinfo=OFFICE_TZ)
        self.month_start = today.replace(day=1)
        self.prev_month_end = self.month_start - timedelta(days=1)
        self.prev_month_start = self.prev_month_end.replace(day=1)
        self.yesterday = today - timedelta(days=1)
        self.week_end = today + timedelta(days=(6 - today.weekday()))
        self.week_start = today - timedelta(days=today.weekday())


def _recruiter_user_id(db: Session, recruiter_id: uuid.UUID) -> uuid.UUID | None:
    row = db.query(Recruiter.user_id).filter(Recruiter.id == recruiter_id).first()
    return row[0] if row else None


def _apply_job_filters(query, filters: _FilterContext, *, job_alias=JobRequirement):
    if filters.recruiter_user_id:
        query = query.filter(job_alias.assigned_to == filters.recruiter_user_id)
    if filters.client_id:
        query = query.filter(job_alias.client_id == filters.client_id)
    if filters.department:
        query = query.filter(job_alias.department == filters.department)
    if filters.job_status:
        query = query.filter(job_alias.status == filters.job_status)
    if filters.location:
        query = query.filter(job_alias.location == filters.location)
    return query


def _month_buckets(months: int = 6) -> list[date]:
    end = date.today().replace(day=1)
    cursor = _add_months(end, -(months - 1))
    out = []
    for _ in range(months):
        out.append(cursor)
        cursor = _add_months(cursor, 1)
    return out


def _add_months(d: date, months: int) -> date:
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def _label_month(d: date) -> str:
    return d.strftime("%b %Y")


def _pct_delta(current: float, previous: float) -> float | None:
    if previous == 0:
        return 100.0 if current > 0 else 0.0 if current == 0 else None
    return round(((current - previous) / previous) * 100, 1)


def _prior_window(start: date, end: date) -> tuple[date, date]:
    """Return the immediately preceding date range with the same duration."""
    days = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    return previous_end - timedelta(days=days - 1), previous_end


def _trend_dir(delta: float | None) -> Literal["up", "down", "flat"]:
    if delta is None or abs(delta) < 0.5:
        return "flat"
    return "up" if delta > 0 else "down"


def _initials(first: str, last: str) -> str:
    return f"{(first or '')[:1]}{(last or '')[:1]}".upper() or "?"


def _minmax(values: list[float], invert: bool = False) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0:
        return [0.0 for _ in values]
    if invert:
        return [round(((hi - v) / span) * 100, 1) for v in values]
    return [round(((v - lo) / span) * 100, 1) for v in values]


def _executive_kpis(
    db: Session,
    filters: _FilterContext,
    leaderboard: list[dict],
) -> list[dict]:
    # Data source: jobs, clients, applications, offers, and placements.
    # Query intent: current operational totals and period rates; utilization is a
    # rule-based share of active recruiters at/above their current average load.
    # Refresh: on request.
    open_jobs_q = _apply_job_filters(
        db.query(func.count(JobRequirement.id)).filter(JobRequirement.status == "open"),
        filters,
    )
    active_open_jobs = int(open_jobs_q.scalar() or 0)

    clients_q = db.query(func.count(Client.id)).filter(Client.status == "active")
    if filters.client_id:
        clients_q = clients_q.filter(Client.id == filters.client_id)
    active_clients = int(clients_q.scalar() or 0)

    pipeline_q = (
        db.query(func.count(CandidateApplication.id))
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(
            CandidateApplication.in_pipeline.is_(True),
            CandidateApplication.owner_status == "approved",
        )
    )
    pipeline_q = _apply_job_filters(pipeline_q, filters)
    in_pipeline = int(pipeline_q.scalar() or 0)

    placements_month = _count_placements(db, filters, start=filters.month_start, end=filters.today)
    placements_prev = _count_placements(
        db, filters, start=filters.prev_month_start, end=filters.prev_month_end
    )

    offer_rate, offer_rate_prev = _offer_acceptance(db, filters)
    tth, tth_prev = _avg_time_to_hire(db, filters)
    conversion, conversion_prev = _candidate_placement_conversion(db, filters)

    utilization = None
    if leaderboard:
        avg_jobs = sum(r["assigned_jobs"] for r in leaderboard) / len(leaderboard)
        utilization = round(
            (sum(1 for r in leaderboard if r["assigned_jobs"] >= avg_jobs) / len(leaderboard)) * 100,
            1,
        )

    spark_placements = _monthly_series_count(db, filters, kind="placements", months=6)

    def kpi(key, label, value, unit, delta, spark, tooltip):
        return {
            "key": key,
            "label": label,
            "value": value,
            "unit": unit,
            "delta_pct": delta,
            "trend": _trend_dir(delta),
            "sparkline": spark,
            "tooltip": tooltip,
        }

    return [
        kpi(
            "active_open_jobs",
            "Active Open Jobs",
            active_open_jobs,
            "number",
            None,
            [],
            "Jobs currently open and accepting submissions.",
        ),
        kpi(
            "active_clients",
            "Active Clients",
            active_clients,
            "number",
            None,
            [],
            "Client accounts marked active.",
        ),
        kpi(
            "candidates_in_pipeline",
            "Total Candidates in Pipeline",
            in_pipeline,
            "number",
            None,
            [],
            "Approved candidates currently moving through hiring stages.",
        ),
        kpi(
            "placements_month",
            "Placements This Month",
            placements_month,
            "number",
            _pct_delta(placements_month, placements_prev),
            spark_placements,
            "Candidates who joined this calendar month.",
        ),
        kpi(
            "offer_acceptance",
            "Offer Acceptance Rate",
            offer_rate,
            "percent",
            _pct_delta(offer_rate, offer_rate_prev)
            if offer_rate is not None and offer_rate_prev is not None
            else None,
            [],
            "Accepted offers divided by total offers in the selected period.",
        ),
        kpi(
            "avg_time_to_hire",
            "Average Time to Hire",
            tth,
            "days",
            _pct_delta(tth, tth_prev) if tth is not None and tth_prev is not None else None,
            [],
            "Average days from submission to join date.",
        ),
        kpi(
            "recruiter_utilization",
            "Recruiters At/Above Avg Load",
            utilization,
            "percent",
            None,
            [],
            "Share of recruiters with assigned open-job load at or above the team average.",
        ),
        kpi(
            "conversion",
            "Candidate-to-Placement Conversion",
            conversion,
            "percent",
            _pct_delta(conversion, conversion_prev)
            if conversion is not None and conversion_prev is not None
            else None,
            [],
            "Placements divided by submissions in the selected period.",
        ),
    ]


def _count_placements(db: Session, filters: _FilterContext, *, start: date, end: date) -> int:
    q = (
        db.query(func.count(Placement.id))
        .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(Placement.joined_date >= start, Placement.joined_date <= end)
    )
    return int(_apply_job_filters(q, filters).scalar() or 0)


def _offer_acceptance(db: Session, filters: _FilterContext) -> tuple[float | None, float | None]:
    def rate(start: date, end: date) -> float | None:
        base = (
            db.query(Offer.status, func.count(Offer.id))
            .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(Offer.offer_date.is_not(None), Offer.offer_date >= start, Offer.offer_date <= end)
        )
        rows = _apply_job_filters(base, filters).group_by(Offer.status).all()
        total = sum(int(c) for _, c in rows)
        accepted = sum(int(c) for s, c in rows if s == "accepted")
        return round((accepted / total) * 100, 1) if total else None

    previous_start, previous_end = _prior_window(filters.start, filters.end)
    return rate(filters.start, filters.end), rate(previous_start, previous_end)


def _avg_time_to_hire(db: Session, filters: _FilterContext) -> tuple[float | None, float | None]:
    def avg(start: date, end: date) -> float | None:
        q = (
            db.query(
                func.avg(
                    Placement.joined_date
                    - func.coalesce(
                        CandidateApplication.applied_date,
                        cast(CandidateApplication.submitted_at, Date),
                    )
                )
            )
            .select_from(Placement)
            .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                Placement.joined_date >= start,
                Placement.joined_date <= end,
                or_(
                    CandidateApplication.applied_date.is_not(None),
                    CandidateApplication.submitted_at.is_not(None),
                ),
            )
        )
        value = _apply_job_filters(q, filters).scalar()
        return round(float(value), 1) if value is not None else None

    previous_start, previous_end = _prior_window(filters.start, filters.end)
    return avg(filters.start, filters.end), avg(previous_start, previous_end)


def _candidate_placement_conversion(
    db: Session, filters: _FilterContext
) -> tuple[float | None, float | None]:
    def rate(start: date, end: date) -> float | None:
        start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc)
        subs = (
            db.query(func.count(CandidateApplication.id))
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                CandidateApplication.submitted_at.is_not(None),
                CandidateApplication.submitted_at >= start_dt,
                CandidateApplication.submitted_at <= end_dt,
            )
        )
        submissions = int(_apply_job_filters(subs, filters).scalar() or 0)
        placements = _count_placements(db, filters, start=start, end=end)
        return round((placements / submissions) * 100, 1) if submissions else None

    previous_start, previous_end = _prior_window(filters.start, filters.end)
    return rate(filters.start, filters.end), rate(previous_start, previous_end)


def _bucket_start(value: date, grain: Literal["weekly", "monthly", "quarterly", "yearly"]) -> date:
    if grain == "weekly":
        return value - timedelta(days=value.weekday())
    if grain == "monthly":
        return value.replace(day=1)
    if grain == "quarterly":
        return value.replace(month=((value.month - 1) // 3) * 3 + 1, day=1)
    return value.replace(month=1, day=1)


def _bucket_label(bucket: date, grain: Literal["weekly", "monthly", "quarterly", "yearly"]) -> str:
    if grain == "weekly":
        return f"W{bucket.isocalendar().week} {bucket.year}"
    if grain == "monthly":
        return _label_month(bucket)
    if grain == "quarterly":
        return f"Q{((bucket.month - 1) // 3) + 1} {bucket.year}"
    return str(bucket.year)


def _time_buckets(
    grain: Literal["weekly", "monthly", "quarterly", "yearly"], count: int
) -> list[date]:
    current = _bucket_start(date.today(), grain)
    if grain == "weekly":
        return [current - timedelta(weeks=index) for index in range(count - 1, -1, -1)]
    if grain == "monthly":
        return _month_buckets(count)
    if grain == "quarterly":
        return [_add_months(current, index * 3) for index in range(-(count - 1), 1)]
    return [current.replace(year=current.year - index) for index in range(count - 1, -1, -1)]


def _activity_dates(
    db: Session,
    filters: _FilterContext,
    kind: Literal["placements", "applications", "interviews", "offers"],
    start: date,
) -> list[date]:
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    if kind == "placements":
        query = (
            db.query(Placement.joined_date)
            .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(Placement.joined_date >= start)
        )
    elif kind == "applications":
        query = (
            db.query(CandidateApplication.submitted_at)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(CandidateApplication.submitted_at >= start_dt)
        )
    elif kind == "interviews":
        query = (
            db.query(Interview.scheduled_datetime)
            .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(Interview.scheduled_datetime >= start_dt)
        )
    else:
        query = (
            db.query(Offer.offer_date)
            .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(Offer.offer_date >= start)
        )

    values = _apply_job_filters(query, filters).all()
    return [value.date() if isinstance(value, datetime) else value for (value,) in values if value]


def _activity_series_count(
    db: Session,
    filters: _FilterContext,
    *,
    kind: Literal["placements", "applications", "interviews", "offers"],
    grain: Literal["weekly", "monthly", "quarterly", "yearly"],
    count: int,
) -> list[dict]:
    buckets = _time_buckets(grain, count)
    counts = {bucket: 0 for bucket in buckets}
    for value in _activity_dates(db, filters, kind, buckets[0]):
        bucket = _bucket_start(value, grain)
        if bucket in counts:
            counts[bucket] += 1
    return [{"label": _bucket_label(bucket, grain), "value": counts[bucket]} for bucket in buckets]


def _monthly_series_count(
    db: Session,
    filters: _FilterContext,
    *,
    kind: Literal["placements", "applications", "interviews", "offers"],
    months: int = 6,
) -> list[dict]:
    return _activity_series_count(db, filters, kind=kind, grain="monthly", count=months)


def _business_trend(
    db: Session,
    filters: _FilterContext,
    *,
    grain: Literal["weekly", "monthly", "quarterly", "yearly"],
) -> dict:
    # Data source: applications, interviews, offers, and placements.
    # Query intent: count each activity in requested time buckets; zero buckets
    # preserve missing history for the UI to report as insufficient data. Refresh: on request.
    periods = {"weekly": 12, "monthly": 6, "quarterly": 8, "yearly": 5}[grain]
    series = [
        {
            "key": "applications",
            "label": "Applications",
            "color": "#7c3aed",
            "points": _activity_series_count(
                db, filters, kind="applications", grain=grain, count=periods
            ),
        },
        {
            "key": "interviews",
            "label": "Interviews",
            "color": "#2563eb",
            "points": _activity_series_count(
                db, filters, kind="interviews", grain=grain, count=periods
            ),
        },
        {
            "key": "offers",
            "label": "Offers",
            "color": "#d97706",
            "points": _activity_series_count(db, filters, kind="offers", grain=grain, count=periods),
        },
        {
            "key": "placements",
            "label": "Placements",
            "color": "#16a34a",
            "points": _activity_series_count(
                db, filters, kind="placements", grain=grain, count=periods
            ),
        },
    ]
    return {"grain": grain, "series": series}


def _hiring_funnel(db: Session, filters: _FilterContext) -> dict:
    # Data source: pipeline_stages, candidate_applications, and job_requirements.
    # Query intent: current approved in-pipeline counts by stage. Conversion/dropoff
    # are snapshot stage ratios, not cohort conversion. Refresh: on request.
    stages = (
        db.query(PipelineStage)
        .filter(PipelineStage.name.in_(FUNNEL_STAGES))
        .order_by(PipelineStage.order_no)
        .all()
    )
    counts: dict[str, int] = {name: 0 for name in FUNNEL_STAGES}
    if stages:
        q = (
            db.query(PipelineStage.name, func.count(CandidateApplication.id))
            .join(CandidateApplication, CandidateApplication.current_stage == PipelineStage.id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                CandidateApplication.in_pipeline.is_(True),
                CandidateApplication.owner_status == "approved",
                PipelineStage.name.in_(FUNNEL_STAGES),
            )
        )
        q = _apply_job_filters(q, filters)
        for name, count in q.group_by(PipelineStage.name).all():
            counts[str(name)] = int(count)

    rows = []
    highest_idx = -1
    highest_drop = -1.0
    for idx, name in enumerate(FUNNEL_STAGES):
        count = counts.get(name, 0)
        prev = counts.get(FUNNEL_STAGES[idx - 1], 0) if idx else None
        conversion = round((count / prev) * 100, 1) if prev else None
        dropoff = round(100 - conversion, 1) if conversion is not None else None
        if dropoff is not None and dropoff > highest_drop:
            highest_drop = dropoff
            highest_idx = idx
        rows.append(
            {
                "name": name,
                "count": count,
                "conversion_pct": conversion,
                "dropoff_pct": dropoff,
                "is_highest_dropoff": False,
            }
        )
    if not any(counts.values()):
        insight = "No candidates currently in the funnel."
    elif highest_idx > 0:
        rows[highest_idx]["is_highest_dropoff"] = True
        insight = (
            f"Snapshot stage count falls most between {FUNNEL_STAGES[highest_idx - 1]} and "
            f"{FUNNEL_STAGES[highest_idx]} ({highest_drop:.0f}% lower than the prior stage)."
        )
    else:
        insight = "Snapshot stage counts do not decline between consecutive stages."
    return {"stages": rows, "insight": insight}


def _recruiter_leaderboard(db: Session, filters: _FilterContext) -> list[dict]:
    # Data source: recruiters/users plus jobs, applications, interviews, offers, and placements.
    # Query intent: per-active-recruiter hiring totals. Productivity is a weighted
    # within-result min/max heuristic; workload uses OVERLOAD_RATIO. Refresh: on request.
    recruiters = (
        db.query(Recruiter, User)
        .join(User, User.id == Recruiter.user_id)
        .filter(Recruiter.status == "active", User.status == "active")
        .order_by(User.first_name, User.last_name)
        .all()
    )
    if filters.recruiter_user_id:
        recruiters = [(r, u) for r, u in recruiters if u.id == filters.recruiter_user_id]

    rows = []
    for recruiter, user in recruiters:
        scoped = _FilterContext(
            start=filters.start,
            end=filters.end,
            today=filters.today,
            recruiter_user_id=user.id,
            client_id=filters.client_id,
            department=filters.department,
            job_status=filters.job_status,
            location=filters.location,
        )
        placements = _count_placements(db, scoped, start=filters.start, end=filters.end)
        active_candidates = int(
            _apply_job_filters(
                db.query(func.count(CandidateApplication.id))
                .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
                .filter(
                    CandidateApplication.in_pipeline.is_(True),
                    CandidateApplication.owner_status == "approved",
                    JobRequirement.assigned_to == user.id,
                ),
                scoped,
            ).scalar()
            or 0
        )
        interviews = int(
            _apply_job_filters(
                db.query(func.count(Interview.id))
                .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
                .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
                .filter(
                    JobRequirement.assigned_to == user.id,
                    Interview.status == "scheduled",
                    Interview.scheduled_datetime >= filters.start_dt,
                    Interview.scheduled_datetime <= filters.end_dt,
                ),
                scoped,
            ).scalar()
            or 0
        )
        offer_rate, _ = _offer_acceptance(db, scoped)
        tth, _ = _avg_time_to_hire(db, scoped)
        assigned_jobs = int(
            _apply_job_filters(
                db.query(func.count(JobRequirement.id)).filter(
                    JobRequirement.assigned_to == user.id,
                    JobRequirement.status == "open",
                ),
                scoped,
            ).scalar()
            or 0
        )
        rows.append(
            {
                "recruiter_id": str(recruiter.id),
                "user_id": str(user.id),
                "name": f"{user.first_name} {user.last_name}".strip(),
                "initials": _initials(user.first_name, user.last_name),
                "placements": placements,
                "active_candidates": active_candidates,
                "interviews_scheduled": interviews,
                "avg_time_to_hire_days": tth,
                "offer_acceptance_rate": offer_rate,
                "assigned_jobs": assigned_jobs,
                "workload_level": "balanced",
                "productivity_score": 0.0,
            }
        )

    if not rows:
        return rows

    p_n = _minmax([float(r["placements"]) for r in rows])
    i_n = _minmax([float(r["interviews_scheduled"]) for r in rows])
    a_n = _minmax([float(r["offer_acceptance_rate"] or 0) for r in rows])
    t_n = _minmax(
        [float(r["avg_time_to_hire_days"]) if r["avg_time_to_hire_days"] is not None else 0 for r in rows],
        invert=True,
    )
    c_n = _minmax([float(r["active_candidates"]) for r in rows])
    avg_jobs = sum(r["assigned_jobs"] for r in rows) / len(rows)

    for idx, row in enumerate(rows):
        score = (
            0.35 * p_n[idx]
            + 0.25 * i_n[idx]
            + 0.15 * a_n[idx]
            + 0.15 * c_n[idx]
            + 0.10 * t_n[idx]
        )
        row["productivity_score"] = round(score, 1)
        jobs = row["assigned_jobs"]
        if avg_jobs and jobs >= avg_jobs * OVERLOAD_RATIO and jobs >= 8:
            row["workload_level"] = "overloaded"
        elif avg_jobs and jobs >= avg_jobs * 1.2:
            row["workload_level"] = "heavy"
        elif jobs <= max(avg_jobs * 0.5, 1):
            row["workload_level"] = "light"
        else:
            row["workload_level"] = "balanced"

    rows.sort(key=lambda r: r["productivity_score"], reverse=True)
    return rows


def _recruiter_workload(db: Session, filters: _FilterContext, leaderboard: list[dict]) -> dict:
    # Data source: recruiter leaderboard (itself derived from recruiter/user and hiring tables).
    # Query intent: order assigned open-job counts and describe rule-based load balance.
    # Refresh: on request.
    bars = [
        {
            "recruiter_id": r["recruiter_id"],
            "name": r["name"],
            "assigned_jobs": r["assigned_jobs"],
            "overloaded": r["workload_level"] == "overloaded",
        }
        for r in sorted(leaderboard, key=lambda x: x["assigned_jobs"], reverse=True)
    ]
    overloaded = [b for b in bars if b["overloaded"]]
    light = [b for b in bars if b["assigned_jobs"] <= 2]
    if not bars:
        insight = ""
    elif overloaded and light:
        insight = (
            f"{overloaded[0]['name']} looks overloaded ({overloaded[0]['assigned_jobs']} open jobs). "
            f"Consider redistributing work to {light[0]['name']}."
        )
    elif overloaded:
        insight = f"{overloaded[0]['name']} has significantly more assigned jobs than peers."
    else:
        insight = "Workload looks balanced across recruiters."
    return {"bars": bars, "insight": insight}


def _client_health(db: Session, filters: _FilterContext) -> list[dict]:
    # Data source: clients, jobs, applications, placements, and client activities.
    # Query intent: account-level operational counts. Health badge is rule-based
    # from client status, activity recency, and PENDING_TOO_LONG_DAYS. Refresh: on request.
    clients = db.query(Client).order_by(Client.company_name).all()
    if filters.client_id:
        clients = [c for c in clients if c.id == filters.client_id]

    cards = []
    for client in clients:
        scoped = _FilterContext(
            start=filters.start,
            end=filters.end,
            today=filters.today,
            recruiter_user_id=filters.recruiter_user_id,
            client_id=client.id,
            department=filters.department,
            job_status=filters.job_status,
            location=filters.location,
        )
        open_positions = int(
            _apply_job_filters(
                db.query(func.coalesce(func.sum(JobRequirement.open_positions), 0)).filter(
                    JobRequirement.status == "open"
                ),
                scoped,
            ).scalar()
            or 0
        )
        placements = _count_placements(db, scoped, start=date(2000, 1, 1), end=filters.today)
        pipeline = int(
            _apply_job_filters(
                db.query(func.count(CandidateApplication.id))
                .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
                .filter(
                    CandidateApplication.in_pipeline.is_(True),
                    CandidateApplication.owner_status == "approved",
                ),
                scoped,
            ).scalar()
            or 0
        )
        tth, _ = _avg_time_to_hire(db, scoped)
        pending_long = int(
            _apply_job_filters(
                db.query(func.count(JobRequirement.id)).filter(
                    JobRequirement.status == "open",
                    JobRequirement.created_at
                    <= datetime.combine(
                        filters.today - timedelta(days=PENDING_TOO_LONG_DAYS),
                        datetime.max.time(),
                        tzinfo=timezone.utc,
                    ),
                ),
                scoped,
            ).scalar()
            or 0
        )
        last_activity = _client_last_activity(db, client.id)
        if client.status != "active":
            badge = "Inactive"
        elif (
            pending_long > 0
            or last_activity is None
            or (filters.today - last_activity).days > 30
        ):
            badge = "Needs Attention"
        else:
            badge = "Healthy"
        cards.append(
            {
                "client_id": str(client.id),
                "name": client.company_name,
                "status_badge": badge,
                "open_positions": open_positions,
                "placements": placements,
                "candidates_in_pipeline": pipeline,
                "avg_hiring_time_days": tth,
                "jobs_pending_too_long": pending_long,
                "last_activity": last_activity.isoformat() if last_activity else None,
                "client_status": client.status,
            }
        )
    return cards


def _client_last_activity(db: Session, client_id: uuid.UUID) -> date | None:
    dates: list[date] = []
    job_created = (
        db.query(func.max(JobRequirement.created_at))
        .filter(JobRequirement.client_id == client_id)
        .scalar()
    )
    if job_created:
        dates.append(job_created.date())
    placement_date = (
        db.query(func.max(Placement.joined_date)).filter(Placement.client_id == client_id).scalar()
    )
    if placement_date:
        dates.append(placement_date)
    app_date = (
        db.query(func.max(CandidateApplication.submitted_at))
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(JobRequirement.client_id == client_id)
        .scalar()
    )
    if app_date:
        dates.append(app_date.date())
    client_activity = (
        db.query(func.max(ClientActivity.created_at))
        .filter(ClientActivity.client_id == client_id)
        .scalar()
    )
    if client_activity:
        dates.append(client_activity.date())
    return max(dates) if dates else None


def _classify_job(jr: JobRequirement, days_open: int) -> tuple[str, bool]:
    if jr.status == "on_hold":
        return "frozen", False
    exceeds = days_open >= SLA_DAYS
    if exceeds:
        return "overdue", True
    if (jr.priority or "").lower() in {"high", "urgent"} or days_open >= URGENT_DAYS:
        return "urgent", exceeds
    return "healthy", False


def _open_job_rows(db: Session, filters: _FilterContext) -> list[dict]:
    # Data source: jobs, clients, assigned users, applications, and pipeline stages.
    # Query intent: open/on-hold requisitions with current candidate counts. Status
    # and SLA flags derive from SLA_DAYS, URGENT_DAYS, priority, and job status. Refresh: on request.
    q = (
        db.query(JobRequirement, Client, User)
        .join(Client, Client.id == JobRequirement.client_id)
        .outerjoin(User, User.id == JobRequirement.assigned_to)
        .filter(JobRequirement.status.in_(["open", "on_hold"]))
    )
    q = _apply_job_filters(q, filters)
    rows = q.order_by(JobRequirement.created_at.asc()).all()

    app_counts = dict(
        db.query(CandidateApplication.job_requirement_id, func.count(CandidateApplication.id))
        .filter(CandidateApplication.in_pipeline.is_(True))
        .group_by(CandidateApplication.job_requirement_id)
        .all()
    )
    stage_rows = (
        db.query(
            CandidateApplication.job_requirement_id,
            PipelineStage.name,
            func.count(CandidateApplication.id),
        )
        .join(PipelineStage, PipelineStage.id == CandidateApplication.current_stage)
        .filter(
            CandidateApplication.in_pipeline.is_(True),
            CandidateApplication.owner_status == "approved",
            PipelineStage.name.in_(BOARD_STAGE_NAMES),
        )
        .group_by(CandidateApplication.job_requirement_id, PipelineStage.name)
        .all()
    )
    top_stage: dict[uuid.UUID, tuple[str, int]] = {}
    for job_id, stage_name, count in stage_rows:
        current = top_stage.get(job_id)
        if not current or int(count) > current[1]:
            top_stage[job_id] = (str(stage_name), int(count))

    out = []
    for jr, client, user in rows:
        created = jr.created_at.date() if jr.created_at else filters.today
        days_open = max((filters.today - created).days, 0)
        status, exceeds = _classify_job(jr, days_open)
        out.append(
            {
                "job_id": str(jr.id),
                "job_title": jr.job_title,
                "client_name": client.company_name,
                "recruiter_name": f"{user.first_name} {user.last_name}".strip() if user else None,
                "days_open": days_open,
                "candidates": int(app_counts.get(jr.id, 0)),
                "current_stage": top_stage.get(jr.id, (None, 0))[0],
                "status": status,
                "exceeds_sla": exceeds,
            }
        )
    out.sort(key=lambda r: (0 if r["exceeds_sla"] else 1, -r["days_open"]))
    return out


def _job_health_counts(jobs: list[dict]) -> dict:
    counts = {"healthy": 0, "urgent": 0, "overdue": 0, "frozen": 0}
    for job in jobs:
        counts[job["status"]] = counts.get(job["status"], 0) + 1
    return counts


def _pipeline_summary(db: Session, filters: _FilterContext) -> list[dict]:
    # Data source: candidates, applications, jobs, pipeline stages, interviews, and offers.
    # Query intent: current-day operational counts with selected yesterday deltas.
    # Refresh: on request.
    today_start = datetime.combine(filters.today, datetime.min.time(), tzinfo=OFFICE_TZ)
    today_end = datetime.combine(filters.today, datetime.max.time(), tzinfo=OFFICE_TZ)
    y_start = datetime.combine(filters.yesterday, datetime.min.time(), tzinfo=OFFICE_TZ)
    y_end = datetime.combine(filters.yesterday, datetime.max.time(), tzinfo=OFFICE_TZ)

    def count_candidates(start_dt, end_dt, status: str | None = None) -> int:
        q = (
            db.query(func.count(func.distinct(Candidate.id)))
            .join(CandidateApplication, CandidateApplication.candidate_id == Candidate.id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                Candidate.created_at >= start_dt,
                Candidate.created_at <= end_dt,
            )
        )
        if status:
            q = q.filter(Candidate.candidate_status == status)
        return int(_apply_job_filters(q, filters).scalar() or 0)

    new_today = count_candidates(today_start, today_end)
    new_y = count_candidates(y_start, y_end)
    rejected_today = count_candidates(today_start, today_end, "rejected")
    rejected_y = count_candidates(y_start, y_end, "rejected")

    interviews_today = int(
        _apply_job_filters(
            db.query(func.count(Interview.id))
            .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                Interview.status == "scheduled",
                Interview.scheduled_datetime >= today_start,
                Interview.scheduled_datetime <= today_end,
            ),
            filters,
        ).scalar()
        or 0
    )
    interviews_y = int(
        _apply_job_filters(
            db.query(func.count(Interview.id))
            .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                Interview.status == "scheduled",
                Interview.scheduled_datetime >= y_start,
                Interview.scheduled_datetime <= y_end,
            ),
            filters,
        ).scalar()
        or 0
    )

    offers_pending = int(
        _apply_job_filters(
            db.query(func.count(Offer.id))
            .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(Offer.status == "pending"),
            filters,
        ).scalar()
        or 0
    )
    joining_week = int(
        _apply_job_filters(
            db.query(func.count(Offer.id))
            .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                Offer.joining_date.is_not(None),
                Offer.joining_date >= filters.today,
                Offer.joining_date <= filters.week_end,
                Offer.status.in_(["pending", "accepted"]),
            ),
            filters,
        ).scalar()
        or 0
    )
    on_hold = int(
        _apply_job_filters(
            db.query(func.count(CandidateApplication.id))
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .join(PipelineStage, PipelineStage.id == CandidateApplication.current_stage)
            .filter(
                CandidateApplication.in_pipeline.is_(True),
                PipelineStage.name == "On Hold",
            ),
            filters,
        ).scalar()
        or 0
    )

    return [
        {"key": "new_today", "label": "New Candidates Today", "value": new_today, "delta": new_today - new_y},
        {"key": "interviews_today", "label": "Interviews Today", "value": interviews_today, "delta": interviews_today - interviews_y},
        {"key": "offers_pending", "label": "Offers Pending", "value": offers_pending, "delta": None},
        {
            "key": "joining_week",
            "label": "Expected Joins This Week",
            "value": joining_week,
            "delta": None,
        },
        {"key": "rejected_today", "label": "Rejected Today", "value": rejected_today, "delta": rejected_today - rejected_y},
        {"key": "on_hold", "label": "Candidates On Hold", "value": on_hold, "delta": None},
    ]


def _activity_feed(db: Session, filters: _FilterContext, *, limit: int = 16) -> list[dict]:
    # Data source: application stage history, users, candidates, pipeline stages, and interviews.
    # Query intent: most recent completed hiring actions, limited by the requested count.
    # Refresh: on request.
    events: list[dict] = []
    now = datetime.now(timezone.utc)

    stage_q = (
        db.query(ApplicationStageHistory, User, Candidate, PipelineStage)
        .join(User, User.id == ApplicationStageHistory.moved_by)
        .join(CandidateApplication, CandidateApplication.id == ApplicationStageHistory.application_id)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .join(PipelineStage, PipelineStage.id == ApplicationStageHistory.stage_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(ApplicationStageHistory.created_at <= now)
        .order_by(ApplicationStageHistory.created_at.desc())
    )
    stage_q = _apply_job_filters(stage_q, filters)
    for hist, user, cand, stage in stage_q.limit(limit).all():
        events.append(
            {
                "id": f"stage-{hist.id}",
                "time": hist.created_at.isoformat() if hist.created_at else None,
                "actor": f"{user.first_name} {user.last_name}".strip(),
                "title": f"Moved candidate to {stage.name}",
                "description": f"{cand.first_name} {cand.last_name}".strip(),
                "type": "stage.move",
            }
        )

    interview_q = (
        db.query(Interview, Candidate, User)
        .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .outerjoin(User, User.id == JobRequirement.assigned_to)
        .filter(
            Interview.status == "completed",
            Interview.scheduled_datetime.is_not(None),
            Interview.scheduled_datetime <= now,
        )
        .order_by(Interview.scheduled_datetime.desc())
    )
    interview_q = _apply_job_filters(interview_q, filters)
    for iv, cand, user in interview_q.limit(limit).all():
        events.append(
            {
                "id": f"iv-{iv.id}",
                "time": iv.scheduled_datetime.isoformat() if iv.scheduled_datetime else None,
                "actor": f"{user.first_name} {user.last_name}".strip() if user else None,
                "title": "Completed interview",
                "description": f"{cand.first_name} {cand.last_name}".strip(),
                "type": "interview.completed",
            }
        )

    events.sort(key=lambda e: e.get("time") or "", reverse=True)
    return events[:limit]


def _alerts(
    db: Session,
    filters: _FilterContext,
    open_jobs: list[dict],
    leaderboard: list[dict],
) -> list[dict]:
    # Data source: open-job rows plus offers, interviews, attendance, jobs, and recruiter rows.
    # Query intent: only emit actionable exceptions from current query results; SLA and
    # inactivity thresholds are rule-based. Refresh: on request.
    alerts: list[dict] = []

    overdue = [j for j in open_jobs if j["exceeds_sla"]]
    if overdue:
        alerts.append(
            {
                "id": "jobs-over-sla",
                "severity": "red",
                "title": f"Jobs open more than {SLA_DAYS} days",
                "description": f"{len(overdue)} roles have exceeded the hiring SLA.",
                "count": len(overdue),
                "action_label": "Review jobs",
                "action_href": "/job-requirements",
            }
        )

    pending_offers = int(
        _apply_job_filters(
            db.query(func.count(Offer.id))
            .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(Offer.status == "pending"),
            filters,
        ).scalar()
        or 0
    )
    if pending_offers:
        alerts.append(
            {
                "id": "offers-pending",
                "severity": "amber",
                "title": "Offers pending approval",
                "description": f"{pending_offers} offers are still pending.",
                "count": pending_offers,
                "action_label": "View pipeline",
                "action_href": "/pipeline",
            }
        )

    reschedule = int(
        _apply_job_filters(
            db.query(func.count(Interview.id))
            .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(Interview.status.in_(["cancelled", "no_show", "on_hold"])),
            filters,
        ).scalar()
        or 0
    )
    if reschedule:
        alerts.append(
            {
                "id": "interviews-reschedule",
                "severity": "amber",
                "title": "Cancelled, no-show, or on-hold interviews",
                "description": f"{reschedule} interviews need follow-up.",
                "count": reschedule,
                "action_label": "Open interviews",
                "action_href": "/pipeline",
            }
        )

    today_start = datetime.combine(filters.today, datetime.min.time(), tzinfo=timezone.utc)
    checked_in = {
        row[0]
        for row in db.query(AttendanceRecord.user_id)
        .filter(AttendanceRecord.date == filters.today, AttendanceRecord.check_in.is_not(None))
        .all()
    }
    inactive = [r for r in leaderboard if uuid.UUID(r["user_id"]) not in checked_in]
    if inactive:
        alerts.append(
            {
                "id": "recruiters-inactive",
                "severity": "amber",
                "title": "Recruiters inactive today",
                "description": f"{len(inactive)} recruiters have not checked in.",
                "count": len(inactive),
                "action_label": "View attendance",
                "action_href": "/",
            }
        )

    unassigned = int(
        _apply_job_filters(
            db.query(func.count(JobRequirement.id)).filter(
                JobRequirement.status == "open", JobRequirement.assigned_to.is_(None)
            ),
            filters,
        ).scalar()
        or 0
    )
    if unassigned:
        alerts.append(
            {
                "id": "jobs-unassigned",
                "severity": "red",
                "title": "Jobs without recruiter assigned",
                "description": f"{unassigned} open jobs have no owner.",
                "count": unassigned,
                "action_label": "Assign recruiters",
                "action_href": "/job-requirements",
            }
        )

    waiting_feedback = int(
        _apply_job_filters(
            db.query(func.count(Interview.id))
            .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                Interview.status == "completed",
                or_(Interview.feedback.is_(None), Interview.feedback == ""),
            ),
            filters,
        ).scalar()
        or 0
    )
    if waiting_feedback:
        alerts.append(
            {
                "id": "feedback-waiting",
                "severity": "amber",
                "title": "Candidates waiting for feedback",
                "description": f"{waiting_feedback} completed interviews lack feedback.",
                "count": waiting_feedback,
                "action_label": "Add feedback",
                "action_href": "/pipeline",
            }
        )

    joining = int(
        _apply_job_filters(
            db.query(func.count(Offer.id))
            .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .filter(
                Offer.joining_date.is_not(None),
                Offer.joining_date >= filters.today,
                Offer.joining_date <= filters.today + timedelta(days=7),
                Offer.status.in_(["pending", "accepted"]),
            ),
            filters,
        ).scalar()
        or 0
    )
    if joining:
        alerts.append(
            {
                "id": "upcoming-joins",
                "severity": "amber",
                "title": "Upcoming joining dates",
                "description": f"{joining} candidates are joining within 7 days.",
                "count": joining,
                "action_label": "Review joins",
                "action_href": "/pipeline",
            }
        )

    return alerts


def _filter_options(db: Session) -> dict:
    # Data source: recruiters/users, clients, and job requirements. Query intent:
    # selectable filter values; job_statuses is the known JobRequirement.status enum,
    # not a live distinct query. Refresh: on request.
    recruiters = (
        db.query(Recruiter.id, User.first_name, User.last_name)
        .join(User, User.id == Recruiter.user_id)
        .filter(Recruiter.status == "active")
        .order_by(User.first_name)
        .all()
    )
    clients = db.query(Client.id, Client.company_name).order_by(Client.company_name).all()
    departments = [
        d
        for (d,) in db.query(JobRequirement.department)
        .filter(JobRequirement.department.is_not(None), func.trim(JobRequirement.department) != "")
        .distinct()
        .order_by(JobRequirement.department)
        .all()
        if d
    ]
    locations = [
        loc
        for (loc,) in db.query(JobRequirement.location)
        .filter(JobRequirement.location.is_not(None), func.trim(JobRequirement.location) != "")
        .distinct()
        .order_by(JobRequirement.location)
        .all()
        if loc
    ]
    return {
        "recruiters": [
            {"id": str(rid), "name": f"{first} {last}".strip()} for rid, first, last in recruiters
        ],
        "clients": [{"id": str(cid), "name": name} for cid, name in clients],
        "departments": departments,
        "locations": locations,
        "job_statuses": ["open", "on_hold", "closed", "filled"],
    }
