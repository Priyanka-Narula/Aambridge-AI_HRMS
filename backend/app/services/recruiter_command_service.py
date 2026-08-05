"""Action-oriented, recruiter-scoped dashboard aggregates."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from statistics import median

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.security import ROLE_RECRUITER, normalize_role
from app.models.job_requirement import JobRequirement
from app.models.offer import Offer
from app.models.pipeline import ApplicationStageHistory, CandidateApplication, Interview
from app.models.user_access import User
from app.services import command_center_service as command

STALE_STAGE_DAYS = 7
PENDING_OFFER_DAYS = 3


def get_recruiter_command(
    db: Session,
    current_user: User,
    *,
    start: date | None = None,
    end: date | None = None,
) -> dict:
    if normalize_role(current_user.role.name) != ROLE_RECRUITER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter access required",
        )

    today = datetime.now(command.OFFICE_TZ).date()
    end = end or today
    start = start or (end - timedelta(days=30))
    personal = command._FilterContext(
        start=start,
        end=end,
        today=today,
        recruiter_user_id=current_user.id,
        client_id=None,
        department=None,
        job_status=None,
        location=None,
    )
    team = command._FilterContext(
        start=start,
        end=end,
        today=today,
        recruiter_user_id=None,
        client_id=None,
        department=None,
        job_status=None,
        location=None,
    )

    leaderboard = command._recruiter_leaderboard(db, team)
    me = next((row for row in leaderboard if row["user_id"] == str(current_user.id)), None)
    rank = next(
        (index for index, row in enumerate(leaderboard, start=1) if row["user_id"] == str(current_user.id)),
        None,
    )
    median_score = (
        round(float(median(row["productivity_score"] for row in leaderboard)), 1)
        if leaderboard
        else 0
    )

    kpis = _personal_kpis(db, current_user, personal)
    focus_counts = _focus_counts(db, current_user, personal)
    open_jobs = command._open_job_rows(db, personal)
    risky_jobs = [
        row
        for row in open_jobs
        if row["status"] != "healthy" or row["candidates"] == 0
    ]

    return {
        "today_focus": _today_focus(focus_counts),
        "kpis": kpis,
        "standing": {
            "rank": rank,
            "total_recruiters": len(leaderboard),
            "team_median_score": median_score,
            "me": me,
            "peers": leaderboard,
        },
        "hiring_funnel": command._hiring_funnel(db, personal),
        "action_queue": _action_queue(focus_counts, risky_jobs),
        "job_health": risky_jobs[:12],
        "personal_trend": command._business_trend(db, personal, grain="monthly"),
    }


def _personal_kpis(db: Session, user: User, filters: command._FilterContext) -> list[dict]:
    owner_kpis = {
        item["key"]: item for item in command._executive_kpis(db, filters, [])
    }
    selected = [
        owner_kpis["placements_month"],
        owner_kpis["conversion"],
        owner_kpis["offer_acceptance"],
        owner_kpis["avg_time_to_hire"],
        owner_kpis["candidates_in_pipeline"],
        owner_kpis["active_open_jobs"],
    ]
    labels = {
        "conversion": "Submission-to-Placement Conversion",
        "candidates_in_pipeline": "Active Pipeline Candidates",
        "active_open_jobs": "Open Assigned Jobs",
    }
    for item in selected:
        item["label"] = labels.get(item["key"], item["label"])

    current, previous = _submission_quality(db, user, filters)
    quality_delta = (
        command._pct_delta(current, previous)
        if current is not None and previous is not None
        else None
    )
    selected.insert(
        4,
        {
            "key": "submission_quality",
            "label": "Submission Quality",
            "value": current,
            "unit": "percent",
            "delta_pct": quality_delta,
            "trend": command._trend_dir(quality_delta),
            "sparkline": [],
            "tooltip": "Owner-approved submissions divided by your submissions in the selected period.",
        },
    )
    return selected


def _submission_quality(
    db: Session,
    user: User,
    filters: command._FilterContext,
) -> tuple[float | None, float | None]:
    def rate(window_start: date, window_end: date) -> float | None:
        start_dt = datetime.combine(window_start, datetime.min.time(), tzinfo=command.OFFICE_TZ)
        end_dt = datetime.combine(window_end, datetime.max.time(), tzinfo=command.OFFICE_TZ)
        rows = (
            db.query(CandidateApplication.owner_status, func.count(CandidateApplication.id))
            .filter(
                CandidateApplication.submitted_by == user.id,
                CandidateApplication.submitted_at >= start_dt,
                CandidateApplication.submitted_at <= end_dt,
            )
            .group_by(CandidateApplication.owner_status)
            .all()
        )
        total = sum(int(count) for _, count in rows)
        approved = sum(int(count) for state, count in rows if state == "approved")
        return round((approved / total) * 100, 1) if total else None

    previous_start, previous_end = command._prior_window(filters.start, filters.end)
    return rate(filters.start, filters.end), rate(previous_start, previous_end)


def _focus_counts(
    db: Session,
    user: User,
    filters: command._FilterContext,
) -> dict[str, int]:
    interviews_today = int(
        db.query(func.count(Interview.id))
        .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(
            JobRequirement.assigned_to == user.id,
            Interview.status == "scheduled",
            Interview.scheduled_datetime >= datetime.combine(
                filters.today, datetime.min.time(), tzinfo=command.OFFICE_TZ
            ),
            Interview.scheduled_datetime <= datetime.combine(
                filters.today, datetime.max.time(), tzinfo=command.OFFICE_TZ
            ),
        )
        .scalar()
        or 0
    )
    pending_reviews = int(
        db.query(func.count(CandidateApplication.id))
        .filter(
            CandidateApplication.submitted_by == user.id,
            CandidateApplication.owner_status == "pending_review",
        )
        .scalar()
        or 0
    )
    pending_offers = int(
        db.query(func.count(Offer.id))
        .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(JobRequirement.assigned_to == user.id, Offer.status == "pending")
        .scalar()
        or 0
    )
    overdue_offers = int(
        db.query(func.count(Offer.id))
        .join(CandidateApplication, CandidateApplication.id == Offer.application_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(
            JobRequirement.assigned_to == user.id,
            Offer.status == "pending",
            Offer.offer_date.is_not(None),
            Offer.offer_date <= filters.today - timedelta(days=PENDING_OFFER_DAYS),
        )
        .scalar()
        or 0
    )
    overdue_feedback = int(
        db.query(func.count(Interview.id))
        .join(CandidateApplication, CandidateApplication.id == Interview.application_id)
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .filter(
            JobRequirement.assigned_to == user.id,
            Interview.status == "completed",
            or_(Interview.feedback.is_(None), func.trim(Interview.feedback) == ""),
        )
        .scalar()
        or 0
    )

    stale_cutoff = datetime.now(command.OFFICE_TZ) - timedelta(days=STALE_STAGE_DAYS)
    latest_moves = (
        db.query(
            ApplicationStageHistory.application_id.label("application_id"),
            func.max(ApplicationStageHistory.created_at).label("last_move"),
        )
        .group_by(ApplicationStageHistory.application_id)
        .subquery()
    )
    stale_candidates = int(
        db.query(func.count(CandidateApplication.id))
        .join(JobRequirement, JobRequirement.id == CandidateApplication.job_requirement_id)
        .outerjoin(latest_moves, latest_moves.c.application_id == CandidateApplication.id)
        .filter(
            JobRequirement.assigned_to == user.id,
            CandidateApplication.in_pipeline.is_(True),
            CandidateApplication.owner_status == "approved",
            or_(
                latest_moves.c.last_move < stale_cutoff,
                latest_moves.c.last_move.is_(None),
            ),
        )
        .scalar()
        or 0
    )
    return {
        "interviews_today": interviews_today,
        "pending_reviews": pending_reviews,
        "pending_offers": pending_offers,
        "overdue_offers": overdue_offers,
        "overdue_feedback": overdue_feedback,
        "expected_joins": command._expected_joins_this_week(db, filters),
        "stale_candidates": stale_candidates,
    }


def _today_focus(counts: dict[str, int]) -> list[dict]:
    return [
        _focus("interviews_today", "Interviews today", counts["interviews_today"], "neutral", "/pipeline"),
        _focus("pending_reviews", "Pending owner reviews", counts["pending_reviews"], "attention", "/job-requirements"),
        _focus("pending_offers", "Offers awaiting response", counts["pending_offers"], "attention", "/pipeline"),
        _focus("expected_joins", "Expected joins this week", counts["expected_joins"], "positive", "/pipeline"),
        _focus("stale_candidates", "Stale pipeline candidates", counts["stale_candidates"], "urgent", "/pipeline"),
    ]


def _focus(key: str, label: str, value: int, tone: str, href: str) -> dict:
    return {"key": key, "label": label, "value": value, "tone": tone, "action_href": href}


def _action_queue(counts: dict[str, int], risky_jobs: list[dict]) -> list[dict]:
    items = [
        _action(
            "feedback",
            "high",
            "Complete interview feedback",
            "Completed interviews are missing feedback.",
            counts["overdue_feedback"],
            "Open pipeline",
            "/pipeline",
        ),
        _action(
            "stale_candidates",
            "high",
            "Move stale candidates forward",
            f"No stage movement for at least {STALE_STAGE_DAYS} days.",
            counts["stale_candidates"],
            "Review candidates",
            "/pipeline",
        ),
        _action(
            "pending_offers",
            "high",
            "Follow up on aging offers",
            f"Pending offers sent at least {PENDING_OFFER_DAYS} days ago.",
            counts["overdue_offers"],
            "Review offers",
            "/pipeline",
        ),
        _action(
            "pending_reviews",
            "medium",
            "Track owner reviews",
            "Your submissions are waiting for an owner decision.",
            counts["pending_reviews"],
            "View requirements",
            "/job-requirements",
        ),
        _action(
            "risky_jobs",
            "medium",
            "Strengthen at-risk jobs",
            "Assigned jobs are overdue, urgent, frozen, or have no pipeline.",
            len(risky_jobs),
            "Review jobs",
            "/job-requirements",
        ),
        _action(
            "expected_joins",
            "low",
            "Confirm expected joins",
            "Candidates are expected to join this week.",
            counts["expected_joins"],
            "Confirm joins",
            "/pipeline",
        ),
    ]
    return [item for item in items if item["count"] > 0]


def _action(
    key: str,
    priority: str,
    title: str,
    description: str,
    count: int,
    action_label: str,
    action_href: str,
) -> dict:
    return {
        "key": key,
        "priority": priority,
        "title": title,
        "description": description,
        "count": count,
        "action_label": action_label,
        "action_href": action_href,
    }
