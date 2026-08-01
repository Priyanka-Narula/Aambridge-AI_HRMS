"""Analytics aggregates for owner and recruiter dashboards."""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import cast, extract, func
from sqlalchemy.orm import Session
from sqlalchemy.types import Date

from app.core.security import ROLE_OWNER, ROLE_RECRUITER, normalize_role
from app.models.candidate import Candidate
from app.models.job_requirement import JobRequirement
from app.models.offer import Offer, Placement
from app.models.pipeline import CandidateApplication, Interview, PipelineStage
from app.models.user_access import Client, Recruiter, User
from app.services.pipeline_service import BOARD_STAGE_NAMES


def _empty() -> list[uuid.UUID]:
    return [uuid.UUID(int=0)]


def _role(user: User) -> str:
    return normalize_role(user.role.name)


def _assigned_job_ids(db: Session, user: User) -> list[uuid.UUID] | None:
    if _role(user) == ROLE_OWNER:
        return None
    if _role(user) != ROLE_RECRUITER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    rows = db.query(JobRequirement.id).filter(JobRequirement.assigned_to == user.id).all()
    return [r[0] for r in rows]


def _recruiter_created_by_keys(user: User) -> list[str]:
    keys = {str(user.id), user.email}
    name = f"{user.first_name} {user.last_name}".strip()
    if name:
        keys.add(name)
    return list(keys)


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _add_months(d: date, months: int) -> date:
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def _label_month(d: date) -> str:
    return d.strftime("%b %Y")


def get_analytics_dashboard(
    db: Session,
    current_user: User,
    *,
    start: date | None = None,
    end: date | None = None,
) -> dict:
    role = _role(current_user)
    today = date.today()
    end = end or today
    start = start or (end - timedelta(days=30))
    job_ids = _assigned_job_ids(db, current_user)
    scoped = job_ids if job_ids is not None else None
    empty = _empty()

    if role == ROLE_OWNER:
        return _owner_dashboard(db, current_user, start=start, end=end)
    return _recruiter_dashboard(
        db,
        current_user,
        start=start,
        end=end,
        job_ids=scoped or empty,
    )


def get_recruiter_performance(
    db: Session,
    *,
    period: Literal["monthly", "till_date"] = "monthly",
    industry: str | None = None,
) -> dict:
    """Return owner-facing recruiter performance metrics, optionally by industry."""
    today = date.today()
    start = _month_start(today) if period == "monthly" else None
    period_start = (
        datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        if start
        else None
    )
    period_end = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)
    month_start = _month_start(today)
    normalized_industry = industry.strip() if industry else None

    industries = [
        value
        for (value,) in (
            db.query(Client.industry)
            .filter(Client.industry.is_not(None), func.trim(Client.industry) != "")
            .distinct()
            .order_by(Client.industry)
            .all()
        )
        if value
    ]

    recruiters = (
        db.query(Recruiter, User)
        .join(User, User.id == Recruiter.user_id)
        .filter(Recruiter.status == "active", User.status == "active")
        .order_by(User.first_name, User.last_name)
        .all()
    )

    def apply_industry_filter(query):
        if normalized_industry:
            return query.filter(Client.industry == normalized_industry)
        return query

    def application_query(user_id: uuid.UUID):
        return apply_industry_filter(
            db.query(CandidateApplication.id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .join(Client, Client.id == JobRequirement.client_id)
            .filter(CandidateApplication.submitted_by == user_id)
        )

    def placement_query(user_id: uuid.UUID):
        return apply_industry_filter(
            db.query(Placement)
            .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .join(Client, Client.id == JobRequirement.client_id)
            .filter(CandidateApplication.submitted_by == user_id, Placement.joined_date.is_not(None))
        )

    def in_submission_period(query):
        query = query.filter(
            CandidateApplication.submitted_at.is_not(None),
            CandidateApplication.submitted_at <= period_end,
        )
        if period_start:
            query = query.filter(CandidateApplication.submitted_at >= period_start)
        return query

    def in_interview_period(query):
        query = query.filter(
            Interview.scheduled_datetime.is_not(None),
            Interview.scheduled_datetime <= period_end,
        )
        if period_start:
            query = query.filter(Interview.scheduled_datetime >= period_start)
        return query

    def in_offer_period(query):
        query = query.filter(Offer.offer_date.is_not(None), Offer.offer_date <= today)
        if start:
            query = query.filter(Offer.offer_date >= start)
        return query

    def in_placement_period(query):
        query = query.filter(Placement.joined_date <= today)
        if start:
            query = query.filter(Placement.joined_date >= start)
        return query

    first_interview_at = (
        db.query(
            Interview.application_id.label("application_id"),
            func.min(Interview.scheduled_datetime).label("scheduled_at"),
        )
        .filter(Interview.scheduled_datetime.is_not(None))
        .group_by(Interview.application_id)
        .subquery()
    )

    result = []
    for recruiter, user in recruiters:
        submissions_total = (
            in_submission_period(application_query(user.id))
            .with_entities(func.count(CandidateApplication.id))
            .scalar()
            or 0
        )
        approved_submissions = (
            in_submission_period(application_query(user.id))
            .filter(CandidateApplication.owner_status == "approved")
            .with_entities(func.count(CandidateApplication.id))
            .scalar()
            or 0
        )
        interviews_total = (
            in_interview_period(
                db.query(func.count(Interview.id))
                .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
                .filter(CandidateApplication.submitted_by == user.id)
            )
        )
        interviews_total = apply_industry_filter(
            interviews_total
            .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
            .join(Client, Client.id == JobRequirement.client_id)
        ).scalar() or 0
        offers_total = (
            in_offer_period(
                db.query(func.count(Offer.id))
                .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
                .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
                .join(Client, Client.id == JobRequirement.client_id)
                .filter(CandidateApplication.submitted_by == user.id)
            )
        )
        offers_total = apply_industry_filter(offers_total).scalar() or 0

        accepted_offers = (
            in_offer_period(
                db.query(func.count(Offer.id))
                .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
                .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
                .join(Client, Client.id == JobRequirement.client_id)
                .filter(
                    CandidateApplication.submitted_by == user.id,
                    Offer.status == "accepted",
                )
            )
        )
        accepted_offers = apply_industry_filter(accepted_offers).scalar() or 0

        period_placements = in_placement_period(placement_query(user.id))
        placements_total = period_placements.count()
        positions_closed_this_month = (
            placement_query(user.id)
            .filter(Placement.joined_date >= month_start, Placement.joined_date <= today)
            .count()
        )
        avg_days = (
            period_placements
            .with_entities(
                func.avg(
                    Placement.joined_date
                    - func.coalesce(
                        CandidateApplication.applied_date,
                        cast(CandidateApplication.submitted_at, Date),
                    )
                )
            )
            .filter(
                CandidateApplication.applied_date.is_not(None)
                | CandidateApplication.submitted_at.is_not(None)
            )
            .scalar()
        )
        avg_response_days = (
            in_submission_period(
                apply_industry_filter(
                    db.query(
                        func.avg(
                            cast(first_interview_at.c.scheduled_at, Date)
                            - cast(CandidateApplication.submitted_at, Date)
                        )
                    )
                    .join(
                        first_interview_at,
                        first_interview_at.c.application_id == CandidateApplication.id,
                    )
                    .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
                    .join(Client, Client.id == JobRequirement.client_id)
                    .filter(
                        CandidateApplication.submitted_by == user.id,
                        first_interview_at.c.scheduled_at >= CandidateApplication.submitted_at,
                    )
                )
            )
            .scalar()
        )
        submission_quality = (
            round((approved_submissions / submissions_total) * 100, 1)
            if submissions_total
            else 0
        )
        offer_acceptance_rate = (
            round((accepted_offers / offers_total) * 100, 1) if offers_total else 0
        )

        result.append(
            {
                "recruiter_id": str(recruiter.id),
                "name": f"{user.first_name} {user.last_name}".strip(),
                "positions_closed_this_month": int(positions_closed_this_month),
                "positions_closed_total": int(placements_total),
                "submissions_total": int(submissions_total),
                "interviews_total": int(interviews_total),
                "offers_total": int(offers_total),
                "approved_submissions": int(approved_submissions),
                "accepted_offers": int(accepted_offers),
                "submission_quality": submission_quality,
                "offer_acceptance_rate": offer_acceptance_rate,
                "conversion_rate": round((placements_total / submissions_total) * 100, 1)
                if submissions_total
                else 0,
                "avg_time_to_hire_days": round(float(avg_days), 1)
                if avg_days is not None
                else None,
                "avg_response_days": round(float(avg_response_days), 1)
                if avg_response_days is not None
                else None,
                "placements_monthly": _recruiter_placements_monthly(
                    db,
                    user_id=user.id,
                    industry=normalized_industry,
                ),
            }
        )

    _score_recruiters(result)
    result.sort(key=lambda item: item["productivity_score"], reverse=True)
    return {"recruiters": result, "industries": industries}


def _score_recruiters(recruiters: list[dict]) -> None:
    """Normalize productivity inputs across the cohort and attach weighted scores."""
    components = {
        "placements": ("positions_closed_total", 0.35, False),
        "interviews": ("interviews_total", 0.25, False),
        "submission_quality": ("submission_quality", 0.15, False),
        "offer_acceptance": ("offer_acceptance_rate", 0.15, False),
        "response_time": ("avg_response_days", 0.10, True),
    }
    normalized: dict[str, dict[str, float]] = {
        str(recruiter["recruiter_id"]): {} for recruiter in recruiters
    }

    for component, (field, _weight, invert) in components.items():
        available = [float(row[field]) for row in recruiters if row[field] is not None]
        minimum = min(available) if available else 0
        maximum = max(available) if available else 0
        span = maximum - minimum
        for recruiter in recruiters:
            value = recruiter[field]
            if value is None or span == 0:
                score = 0.0
            elif invert:
                score = ((maximum - float(value)) / span) * 100
            else:
                score = ((float(value) - minimum) / span) * 100
            normalized[str(recruiter["recruiter_id"])][component] = round(score, 1)

    for recruiter in recruiters:
        breakdown = normalized[str(recruiter["recruiter_id"])]
        score = sum(
            breakdown[component] * weight
            for component, (_field, weight, _invert) in components.items()
        )
        recruiter["score_breakdown"] = breakdown
        recruiter["productivity_score"] = round(score, 1)


def _recruiter_placements_monthly(
    db: Session,
    *,
    user_id: uuid.UUID,
    industry: str | None,
    months: int = 6,
) -> list[dict]:
    end = _month_start(date.today())
    start = _add_months(end, -(months - 1))
    query = (
        db.query(
            extract("year", Placement.joined_date).label("y"),
            extract("month", Placement.joined_date).label("m"),
            func.count(Placement.id),
        )
        .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .join(Client, Client.id == JobRequirement.client_id)
        .filter(
            CandidateApplication.submitted_by == user_id,
            Placement.joined_date >= start,
        )
    )
    if industry:
        query = query.filter(Client.industry == industry)
    keyed = {(int(y), int(m)): int(count) for y, m, count in query.group_by("y", "m").all()}
    cursor = start
    values = []
    for _ in range(months):
        values.append({"label": _label_month(cursor), "value": keyed.get((cursor.year, cursor.month), 0)})
        cursor = _add_months(cursor, 1)
    return values


def _owner_dashboard(db: Session, user: User, *, start: date, end: date) -> dict:
    # ── Candidate KPIs (GROUP BY status once) ──────────────────────────────
    status_rows = (
        db.query(Candidate.candidate_status, func.count(Candidate.id))
        .group_by(Candidate.candidate_status)
        .all()
    )
    status_map = {str(s or "unknown"): int(c) for s, c in status_rows}
    total_candidates = sum(status_map.values())
    active_candidates = status_map.get("active", 0)
    inactive_candidates = status_map.get("inactive", 0)
    pending_approval = status_map.get("pending_approval", 0)
    rejected_candidates = status_map.get("rejected", 0)
    # "Approved" talent = active + interviewing + offered + hired
    approved_candidates = sum(
        status_map.get(k, 0) for k in ("active", "interviewing", "offered", "hired")
    )

    # Submission owner decisions
    owner_status_rows = (
        db.query(CandidateApplication.owner_status, func.count(CandidateApplication.id))
        .group_by(CandidateApplication.owner_status)
        .all()
    )
    owner_status_map = {str(s): int(c) for s, c in owner_status_rows}

    # Recruiters / clients / jobs
    total_recruiters = db.query(func.count(Recruiter.id)).scalar() or 0
    active_recruiters = (
        db.query(func.count(Recruiter.id)).filter(Recruiter.status == "active").scalar() or 0
    )
    total_clients = db.query(func.count(Client.id)).scalar() or 0
    open_jobs = (
        db.query(func.count(JobRequirement.id))
        .filter(JobRequirement.status == "open")
        .scalar()
        or 0
    )
    closed_jobs = (
        db.query(func.count(JobRequirement.id))
        .filter(JobRequirement.status.in_(["closed", "filled"]))
        .scalar()
        or 0
    )

    placements_total = db.query(func.count(Placement.id)).scalar() or 0
    month_start = _month_start(date.today())
    monthly_placements = (
        db.query(func.count(Placement.id))
        .filter(Placement.joined_date >= month_start)
        .scalar()
        or 0
    )
    revenue = (
        db.query(func.coalesce(func.sum(Placement.revenue_generated), 0))
        .scalar()
    )
    revenue_value = float(revenue or 0)

    # Average time to hire (days): joined_date - submitted_at::date
    avg_days = (
        db.query(
            func.avg(
                Placement.joined_date
                - cast(CandidateApplication.submitted_at, Date)
            )
        )
        .select_from(Placement)
        .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
        .filter(
            Placement.joined_date.is_not(None),
            CandidateApplication.submitted_at.is_not(None),
        )
        .scalar()
    )
    avg_time_to_hire = round(float(avg_days), 1) if avg_days is not None else None

    pipeline_stages = _pipeline_stage_counts(db, job_ids=None)
    candidate_status_chart = [
        {"label": label, "value": status_map.get(key, 0)}
        for label, key in [
            ("Active", "active"),
            ("Inactive", "inactive"),
            ("Pending", "pending_approval"),
            ("Interviewing", "interviewing"),
            ("Offered", "offered"),
            ("Rejected", "rejected"),
            ("Hired", "hired"),
        ]
        if status_map.get(key, 0) > 0 or key in ("active", "inactive", "pending_approval")
    ]

    recruiter_performance = _recruiter_performance(db)
    client_placements = _client_placements(db)
    heatmap = _recruiter_activity_heatmap(db, start=start, end=end)
    uploads_monthly = _candidate_uploads_monthly(db, months=6)
    placements_monthly = _placements_monthly(db, months=6)

    recent_placements = _recent_placements(db, limit=8)
    recent_activities = _recent_activities(db, limit=12)
    notifications = recent_activities[:8]

    return {
        "role": "owner",
        "kpis": {
            "total_candidates": total_candidates,
            "active_candidates": active_candidates,
            "inactive_candidates": inactive_candidates,
            "pending_approval": pending_approval,
            "approved_candidates": approved_candidates,
            "rejected_candidates": rejected_candidates,
            "submissions_pending": owner_status_map.get("pending_review", 0),
            "submissions_approved": owner_status_map.get("approved", 0),
            "submissions_rejected": owner_status_map.get("rejected", 0),
            "total_recruiters": int(total_recruiters),
            "active_recruiters": int(active_recruiters),
            "total_clients": int(total_clients),
            "open_jobs": int(open_jobs),
            "closed_jobs": int(closed_jobs),
            "placements": int(placements_total),
            "monthly_placements": int(monthly_placements),
            "revenue": revenue_value,
            "average_time_to_hire_days": avg_time_to_hire,
            "in_pipeline": sum(s["count"] for s in pipeline_stages),
        },
        "charts": {
            "pipeline_stages": pipeline_stages,
            "candidate_status": candidate_status_chart,
            "recruiter_performance": recruiter_performance,
            "client_placements": client_placements,
            "recruiter_activity_heatmap": heatmap,
            "candidate_uploads_monthly": uploads_monthly,
            "placements_monthly": placements_monthly,
            "interviews_vs_offers": [],
        },
        "tables": {
            "recent_placements": recent_placements,
            "recent_activities": recent_activities,
            "notifications": notifications,
            "recent_candidates": [],
            "pending_tasks": _owner_pending_tasks(db, limit=8),
            "todays_interviews": _todays_interviews(db, job_ids=None, limit=10),
            "upcoming_interviews": _upcoming_interviews(db, job_ids=None, limit=14),
            "recent_feedback": [],
        },
    }


def _recruiter_dashboard(
    db: Session,
    user: User,
    *,
    start: date,
    end: date,
    job_ids: list[uuid.UUID],
) -> dict:
    created_keys = _recruiter_created_by_keys(user)

    status_rows = (
        db.query(Candidate.candidate_status, func.count(Candidate.id))
        .filter(Candidate.created_by.in_(created_keys))
        .group_by(Candidate.candidate_status)
        .all()
    )
    status_map = {str(s or "unknown"): int(c) for s, c in status_rows}
    my_candidates = sum(status_map.values())

    owner_rows = (
        db.query(CandidateApplication.owner_status, func.count(CandidateApplication.id))
        .filter(
            CandidateApplication.job_requirement_id.in_(job_ids),
            CandidateApplication.submitted_by == user.id,
        )
        .group_by(CandidateApplication.owner_status)
        .all()
    )
    owner_map = {str(s): int(c) for s, c in owner_rows}

    interviews_scheduled = (
        db.query(func.count(Interview.id))
        .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
        .filter(
            CandidateApplication.job_requirement_id.in_(job_ids),
            Interview.status == "scheduled",
        )
        .scalar()
        or 0
    )
    offers = (
        db.query(func.count(Offer.id))
        .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
        .filter(
            CandidateApplication.job_requirement_id.in_(job_ids),
            Offer.status.in_(["pending", "accepted"]),
        )
        .scalar()
        or 0
    )
    placements = (
        db.query(func.count(Placement.id))
        .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
        .filter(CandidateApplication.job_requirement_id.in_(job_ids))
        .scalar()
        or 0
    )
    jobs_assigned = (
        db.query(func.count(JobRequirement.id))
        .filter(JobRequirement.assigned_to == user.id)
        .scalar()
        or 0
    )
    clients_assigned = (
        db.query(func.count(func.distinct(JobRequirement.client_id)))
        .filter(JobRequirement.assigned_to == user.id)
        .scalar()
        or 0
    )

    pipeline_stages = _pipeline_stage_counts(db, job_ids=job_ids)
    candidate_status_chart = [
        {"label": label, "value": status_map.get(key, 0)}
        for label, key in [
            ("Active", "active"),
            ("Inactive", "inactive"),
            ("Pending", "pending_approval"),
            ("Rejected", "rejected"),
        ]
    ]
    uploads_monthly = _candidate_uploads_monthly(db, months=6, created_by_keys=created_keys)
    placements_monthly = _placements_monthly(db, months=6, job_ids=job_ids)
    interviews_vs_offers = [
        {"label": "Interviews", "value": int(interviews_scheduled)},
        {"label": "Offers", "value": int(offers)},
        {"label": "Placements", "value": int(placements)},
    ]

    return {
        "role": "recruiter",
        "kpis": {
            "my_candidates": my_candidates,
            "pending_approval": owner_map.get("pending_review", 0) + status_map.get("pending_approval", 0),
            "approved": owner_map.get("approved", 0),
            "rejected": owner_map.get("rejected", 0) + status_map.get("rejected", 0),
            "interviews_scheduled": int(interviews_scheduled),
            "offers": int(offers),
            "placements": int(placements),
            "clients_assigned": int(clients_assigned),
            "jobs_assigned": int(jobs_assigned),
            "in_pipeline": sum(s["count"] for s in pipeline_stages),
            # Keep owner-shaped zeros for shared typing convenience
            "total_candidates": my_candidates,
            "active_candidates": status_map.get("active", 0),
            "inactive_candidates": status_map.get("inactive", 0),
            "approved_candidates": status_map.get("active", 0),
            "rejected_candidates": status_map.get("rejected", 0),
            "submissions_pending": owner_map.get("pending_review", 0),
            "submissions_approved": owner_map.get("approved", 0),
            "submissions_rejected": owner_map.get("rejected", 0),
            "total_recruiters": 0,
            "active_recruiters": 0,
            "total_clients": int(clients_assigned),
            "open_jobs": int(
                db.query(func.count(JobRequirement.id))
                .filter(
                    JobRequirement.assigned_to == user.id,
                    JobRequirement.status == "open",
                )
                .scalar()
                or 0
            ),
            "closed_jobs": int(
                db.query(func.count(JobRequirement.id))
                .filter(
                    JobRequirement.assigned_to == user.id,
                    JobRequirement.status.in_(["closed", "filled"]),
                )
                .scalar()
                or 0
            ),
            "monthly_placements": int(
                db.query(func.count(Placement.id))
                .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
                .filter(
                    CandidateApplication.job_requirement_id.in_(job_ids),
                    Placement.joined_date >= _month_start(date.today()),
                )
                .scalar()
                or 0
            ),
            "revenue": 0.0,
            "average_time_to_hire_days": None,
        },
        "charts": {
            "pipeline_stages": pipeline_stages,
            "candidate_status": candidate_status_chart,
            "recruiter_performance": [],
            "client_placements": _client_placements(db, job_ids=job_ids),
            "recruiter_activity_heatmap": _recruiter_activity_heatmap(
                db, start=start, end=end, user_id=user.id
            ),
            "candidate_uploads_monthly": uploads_monthly,
            "placements_monthly": placements_monthly,
            "interviews_vs_offers": interviews_vs_offers,
        },
        "tables": {
            "recent_placements": _recent_placements(db, limit=8, job_ids=job_ids),
            "recent_activities": _recent_activities(db, limit=12, job_ids=job_ids, user_id=user.id),
            "notifications": _recent_activities(db, limit=8, job_ids=job_ids, user_id=user.id),
            "recent_candidates": _recent_candidates(db, created_by_keys=created_keys, limit=8),
            "pending_tasks": _recruiter_pending_tasks(db, user=user, job_ids=job_ids, limit=8),
            "todays_interviews": _todays_interviews(db, job_ids=job_ids, limit=10),
            "upcoming_interviews": _upcoming_interviews(db, job_ids=job_ids, limit=14),
            "recent_feedback": _recent_feedback(db, job_ids=job_ids, limit=6),
        },
    }


def _pipeline_stage_counts(db: Session, job_ids: list[uuid.UUID] | None) -> list[dict]:
    stages = (
        db.query(PipelineStage)
        .filter(PipelineStage.name.in_(BOARD_STAGE_NAMES))
        .order_by(PipelineStage.order_no)
        .all()
    )
    if not stages:
        return []
    q = (
        db.query(CandidateApplication.current_stage, func.count(CandidateApplication.id))
        .filter(
            CandidateApplication.in_pipeline.is_(True),
            CandidateApplication.owner_status == "approved",
            CandidateApplication.current_stage.in_([s.id for s in stages]),
        )
    )
    if job_ids is not None:
        q = q.filter(CandidateApplication.job_requirement_id.in_(job_ids or _empty()))
    counts = {sid: int(c) for sid, c in q.group_by(CandidateApplication.current_stage).all()}
    return [
        {"name": s.name, "count": counts.get(s.id, 0), "order_no": s.order_no}
        for s in stages
    ]


def _recruiter_performance(db: Session, limit: int = 8) -> list[dict]:
    rows = (
        db.query(
            User.first_name,
            User.last_name,
            func.count(Placement.id),
        )
        .select_from(JobRequirement)
        .join(User, User.id == JobRequirement.assigned_to)
        .join(CandidateApplication, CandidateApplication.job_requirement_id == JobRequirement.id)
        .join(Placement, Placement.application_id == CandidateApplication.id)
        .group_by(User.id, User.first_name, User.last_name)
        .order_by(func.count(Placement.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "label": f"{first} {last}".strip(),
            "value": int(count),
        }
        for first, last, count in rows
    ]


def _client_placements(db: Session, job_ids: list[uuid.UUID] | None = None, limit: int = 8) -> list[dict]:
    q = (
        db.query(Client.company_name, func.count(Placement.id))
        .select_from(Placement)
        .join(Client, Client.id == Placement.client_id)
    )
    if job_ids is not None:
        q = q.join(
            CandidateApplication, CandidateApplication.id == Placement.application_id
        ).filter(CandidateApplication.job_requirement_id.in_(job_ids or _empty()))
    rows = (
        q.group_by(Client.id, Client.company_name)
        .order_by(func.count(Placement.id).desc())
        .limit(limit)
        .all()
    )
    return [{"label": name, "value": int(count)} for name, count in rows]


def _candidate_uploads_monthly(
    db: Session,
    *,
    months: int = 6,
    created_by_keys: list[str] | None = None,
) -> list[dict]:
    end = _month_start(date.today())
    start = _add_months(end, -(months - 1))
    q = db.query(
        extract("year", Candidate.created_at).label("y"),
        extract("month", Candidate.created_at).label("m"),
        func.count(Candidate.id),
    ).filter(Candidate.created_at >= datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc))
    if created_by_keys:
        q = q.filter(Candidate.created_by.in_(created_by_keys))
    rows = q.group_by("y", "m").all()
    keyed = {(int(y), int(m)): int(c) for y, m, c in rows}
    out = []
    cursor = start
    for _ in range(months):
        out.append(
            {
                "label": _label_month(cursor),
                "value": keyed.get((cursor.year, cursor.month), 0),
            }
        )
        cursor = _add_months(cursor, 1)
    return out


def _placements_monthly(
    db: Session,
    *,
    months: int = 6,
    job_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    end = _month_start(date.today())
    start = _add_months(end, -(months - 1))
    q = db.query(
        extract("year", Placement.joined_date).label("y"),
        extract("month", Placement.joined_date).label("m"),
        func.count(Placement.id),
    ).filter(Placement.joined_date >= start)
    if job_ids is not None:
        q = q.join(
            CandidateApplication, CandidateApplication.id == Placement.application_id
        ).filter(CandidateApplication.job_requirement_id.in_(job_ids or _empty()))
    rows = q.group_by("y", "m").all()
    keyed = {(int(y), int(m)): int(c) for y, m, c in rows}
    out = []
    cursor = start
    for _ in range(months):
        out.append(
            {
                "label": _label_month(cursor),
                "value": keyed.get((cursor.year, cursor.month), 0),
            }
        )
        cursor = _add_months(cursor, 1)
    return out


def _recruiter_activity_heatmap(
    db: Session,
    *,
    start: date,
    end: date,
    user_id: uuid.UUID | None = None,
) -> list[dict]:
    """Dow (0=Mon) × hour buckets from submission timestamps."""
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc)
    q = db.query(
        extract("isodow", CandidateApplication.submitted_at).label("dow"),
        extract("hour", CandidateApplication.submitted_at).label("hour"),
        func.count(CandidateApplication.id),
    ).filter(
        CandidateApplication.submitted_at.is_not(None),
        CandidateApplication.submitted_at >= start_dt,
        CandidateApplication.submitted_at <= end_dt,
    )
    if user_id is not None:
        q = q.filter(CandidateApplication.submitted_by == user_id)
    rows = q.group_by("dow", "hour").all()
    # Normalize isodow 1-7 → 0-6
    cells = [
        {"dow": int(dow) - 1, "hour": int(hour), "value": int(count)}
        for dow, hour, count in rows
        if dow is not None and hour is not None
    ]
    return cells


def _recent_placements(
    db: Session,
    *,
    limit: int = 8,
    job_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    q = (
        db.query(Placement, Candidate, Client, JobRequirement)
        .join(Candidate, Candidate.id == Placement.candidate_id)
        .join(Client, Client.id == Placement.client_id)
        .join(CandidateApplication, CandidateApplication.id == Placement.application_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(Placement.joined_date.is_not(None))
        .order_by(Placement.joined_date.desc())
    )
    if job_ids is not None:
        q = q.filter(CandidateApplication.job_requirement_id.in_(job_ids or _empty()))
    rows = q.limit(limit).all()
    return [
        {
            "id": str(p.id),
            "candidate_name": f"{c.first_name} {c.last_name}".strip(),
            "client_name": client.company_name,
            "job_title": jr.job_title,
            "joined_date": p.joined_date.isoformat() if p.joined_date else None,
            "revenue": float(p.revenue_generated) if p.revenue_generated is not None else None,
        }
        for p, c, client, jr in rows
    ]


def _recent_activities(
    db: Session,
    *,
    limit: int = 12,
    job_ids: list[uuid.UUID] | None = None,
    user_id: uuid.UUID | None = None,
) -> list[dict]:
    events: list[dict] = []

    # Recent candidates
    cq = db.query(Candidate).order_by(Candidate.created_at.desc())
    if user_id is not None:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            cq = cq.filter(Candidate.created_by.in_(_recruiter_created_by_keys(user)))
    for c in cq.limit(limit).all():
        events.append(
            {
                "id": f"cand-{c.id}",
                "type": "candidate.uploaded",
                "title": "Candidate uploaded",
                "description": f"{c.first_name} {c.last_name}".strip(),
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "actor": c.created_by,
            }
        )

    # Owner decisions
    aq = (
        db.query(CandidateApplication, Candidate)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .filter(CandidateApplication.owner_status.in_(["approved", "rejected"]))
        .order_by(CandidateApplication.submitted_at.desc())
    )
    if job_ids is not None:
        aq = aq.filter(CandidateApplication.job_requirement_id.in_(job_ids or _empty()))
    for app, cand in aq.limit(limit).all():
        kind = (
            "candidate.approved"
            if app.owner_status == "approved"
            else "candidate.rejected"
        )
        events.append(
            {
                "id": f"app-{app.id}",
                "type": kind,
                "title": "Candidate approved" if kind.endswith("approved") else "Candidate rejected",
                "description": f"{cand.first_name} {cand.last_name}".strip(),
                "created_at": app.submitted_at.isoformat() if app.submitted_at else None,
                "actor": "Owner",
            }
        )

    # Placements
    for row in _recent_placements(db, limit=limit, job_ids=job_ids):
        events.append(
            {
                "id": f"place-{row['id']}",
                "type": "placement.completed",
                "title": "Placement completed",
                "description": f"{row['candidate_name']} · {row['client_name']}",
                "created_at": row["joined_date"],
                "actor": None,
            }
        )

    # Closed jobs
    jq = (
        db.query(JobRequirement)
        .filter(JobRequirement.status.in_(["closed", "filled"]))
        .order_by(JobRequirement.created_at.desc())
    )
    if job_ids is not None:
        jq = jq.filter(JobRequirement.id.in_(job_ids or _empty()))
    for jr in jq.limit(limit).all():
        events.append(
            {
                "id": f"job-{jr.id}",
                "type": "job.closed",
                "title": "Job closed",
                "description": jr.job_title,
                "created_at": jr.created_at.isoformat() if jr.created_at else None,
                "actor": None,
            }
        )

    # New clients (owner-only feed; recruiters skip company-wide client list)
    if job_ids is None:
        for client in (
            db.query(Client).order_by(Client.created_at.desc()).limit(limit).all()
        ):
            events.append(
                {
                    "id": f"client-{client.id}",
                    "type": "client.created",
                    "title": "Client created",
                    "description": client.company_name,
                    "created_at": client.created_at.isoformat() if client.created_at else None,
                    "actor": None,
                }
            )

    events.sort(key=lambda e: e.get("created_at") or "", reverse=True)
    return events[:limit]


def _recent_candidates(db: Session, *, created_by_keys: list[str], limit: int) -> list[dict]:
    rows = (
        db.query(Candidate)
        .filter(Candidate.created_by.in_(created_by_keys))
        .order_by(Candidate.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(c.id),
            "name": f"{c.first_name} {c.last_name}".strip(),
            "email": c.email,
            "status": c.candidate_status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in rows
    ]


def _owner_pending_tasks(db: Session, *, limit: int) -> list[dict]:
    rows = (
        db.query(CandidateApplication, Candidate, JobRequirement)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(CandidateApplication.owner_status == "pending_review")
        .order_by(CandidateApplication.submitted_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(app.id),
            "title": f"Review {cand.first_name} {cand.last_name}".strip(),
            "subtitle": jr.job_title,
            "status": "pending_review",
            "created_at": app.submitted_at.isoformat() if app.submitted_at else None,
        }
        for app, cand, jr in rows
    ]


def _recruiter_pending_tasks(
    db: Session,
    *,
    user: User,
    job_ids: list[uuid.UUID],
    limit: int,
) -> list[dict]:
    tasks: list[dict] = []
    pending = (
        db.query(CandidateApplication, Candidate, JobRequirement)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(
            CandidateApplication.job_requirement_id.in_(job_ids),
            CandidateApplication.submitted_by == user.id,
            CandidateApplication.owner_status == "pending_review",
        )
        .order_by(CandidateApplication.submitted_at.desc())
        .limit(limit)
        .all()
    )
    for app, cand, jr in pending:
        tasks.append(
            {
                "id": str(app.id),
                "title": f"Awaiting approval · {cand.first_name} {cand.last_name}".strip(),
                "subtitle": jr.job_title,
                "status": "pending_review",
                "created_at": app.submitted_at.isoformat() if app.submitted_at else None,
            }
        )
    return tasks[:limit]


def _todays_interviews(
    db: Session,
    *,
    job_ids: list[uuid.UUID] | None,
    limit: int,
) -> list[dict]:
    start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(date.today(), datetime.max.time(), tzinfo=timezone.utc)
    q = (
        db.query(Interview, CandidateApplication, Candidate, JobRequirement)
        .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(
            Interview.scheduled_datetime.is_not(None),
            Interview.scheduled_datetime >= start,
            Interview.scheduled_datetime <= end,
        )
        .order_by(Interview.scheduled_datetime.asc())
    )
    if job_ids is not None:
        q = q.filter(CandidateApplication.job_requirement_id.in_(job_ids or _empty()))
    rows = q.limit(limit).all()
    return [
        {
            "id": str(iv.id),
            "candidate_name": f"{cand.first_name} {cand.last_name}".strip(),
            "job_title": jr.job_title,
            "scheduled_at": iv.scheduled_datetime.isoformat() if iv.scheduled_datetime else None,
            "mode": iv.mode,
            "interviewer_name": iv.interviewer_name,
            "status": iv.status,
        }
        for iv, app, cand, jr in rows
    ]


def _upcoming_interviews(
    db: Session,
    *,
    job_ids: list[uuid.UUID] | None,
    limit: int,
    days: int = 14,
) -> list[dict]:
    start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(date.today() + timedelta(days=days), datetime.max.time(), tzinfo=timezone.utc)
    q = (
        db.query(Interview, CandidateApplication, Candidate, JobRequirement)
        .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(
            Interview.scheduled_datetime.is_not(None),
            Interview.scheduled_datetime >= start,
            Interview.scheduled_datetime <= end,
            Interview.status.in_(["scheduled", "completed"]),
        )
        .order_by(Interview.scheduled_datetime.asc())
    )
    if job_ids is not None:
        q = q.filter(CandidateApplication.job_requirement_id.in_(job_ids or _empty()))
    rows = q.limit(limit).all()
    return [
        {
            "id": str(iv.id),
            "candidate_name": f"{cand.first_name} {cand.last_name}".strip(),
            "job_title": jr.job_title,
            "scheduled_at": iv.scheduled_datetime.isoformat() if iv.scheduled_datetime else None,
            "mode": iv.mode,
            "interviewer_name": iv.interviewer_name,
            "status": iv.status,
        }
        for iv, app, cand, jr in rows
    ]


def _recent_feedback(db: Session, *, job_ids: list[uuid.UUID], limit: int) -> list[dict]:
    rows = (
        db.query(Interview, Candidate, JobRequirement)
        .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(
            CandidateApplication.job_requirement_id.in_(job_ids or _empty()),
            Interview.feedback.is_not(None),
            Interview.feedback != "",
        )
        .order_by(Interview.scheduled_datetime.desc().nullslast())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(iv.id),
            "candidate_name": f"{cand.first_name} {cand.last_name}".strip(),
            "job_title": jr.job_title,
            "feedback": (iv.feedback or "")[:240],
            "scheduled_at": iv.scheduled_datetime.isoformat() if iv.scheduled_datetime else None,
        }
        for iv, cand, jr in rows
    ]


def get_dashboard_notifications(
    db: Session,
    current_user: User,
    *,
    limit: int = 12,
) -> dict:
    role = _role(current_user)
    job_ids = _assigned_job_ids(db, current_user)
    scoped = job_ids if job_ids is not None else None
    if role == ROLE_OWNER:
        items = _recent_activities(db, limit=limit)
    else:
        items = _recent_activities(
            db,
            limit=limit,
            job_ids=scoped or _empty(),
            user_id=current_user.id,
        )
    return {
        "items": items[:limit],
        "unread_count": len(items[:limit]),
    }


# Backwards-compatible alias used by earlier route
def get_dashboard_stats(db: Session, current_user: User, *, start: date | None = None, end: date | None = None) -> dict:
    return get_analytics_dashboard(db, current_user, start=start, end=end)
