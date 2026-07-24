"""Hiring pipeline: shortlist after client feedback, stage progression to joining."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import ROLE_OWNER, ROLE_RECRUITER, normalize_role
from app.models.candidate import Candidate
from app.models.job_requirement import JobRequirement
from app.models.offer import Offer, Placement
from app.models.pipeline import ApplicationStageHistory, CandidateApplication, PipelineStage
from app.models.user_access import Client, Recruiter, User
from app.services.email_service import email_configured, send_email_with_attachment

# Stages shown on the active hiring board (excludes Applied — that lives in Submissions).
BOARD_STAGE_NAMES = [
    "Shortlisted",
    "Screening",
    "Interview",
    "Offer",
    "Joined",
    "On Hold",
    "Rejected",
]

STAGE_SHORTLISTED = "Shortlisted"
STAGE_OFFER = "Offer"
STAGE_JOINED = "Joined"
STAGE_REJECTED = "Rejected"
STAGE_ON_HOLD = "On Hold"

# Main hiring path — only forward moves (plus On Hold / Rejected exits).
FORWARD_ORDER = ["Shortlisted", "Screening", "Interview", "Offer", "Joined"]


def allowed_stage_targets(current_name: str) -> set[str]:
    """Return stages that are allowed from current (no moving backwards)."""
    if current_name in (STAGE_JOINED, STAGE_REJECTED):
        return set()
    if current_name == STAGE_ON_HOLD:
        # Resume only into the active hiring path (not Rejected→back); Rejected is exit.
        return set(FORWARD_ORDER) | {STAGE_REJECTED}
    if current_name in FORWARD_ORDER:
        idx = FORWARD_ORDER.index(current_name)
        return set(FORWARD_ORDER[idx + 1 :]) | {STAGE_ON_HOLD, STAGE_REJECTED}
    if current_name == "Applied":
        return {STAGE_SHORTLISTED}
    return set()


# Kept for callers / docs; derived from forward-only rules.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    name: allowed_stage_targets(name)
    for name in [*FORWARD_ORDER, STAGE_ON_HOLD, STAGE_REJECTED, "Applied"]
}


def _get_stage_by_name(db: Session, name: str) -> PipelineStage:
    stage = db.query(PipelineStage).filter(PipelineStage.name == name).first()
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline stage '{name}' is not configured. Run alembic upgrade head.",
        )
    return stage


def list_pipeline_stages(db: Session) -> list[PipelineStage]:
    return (
        db.query(PipelineStage)
        .filter(PipelineStage.name.in_(BOARD_STAGE_NAMES))
        .order_by(PipelineStage.order_no)
        .all()
    )


def _load_app_for_pipeline(db: Session, app_id: uuid.UUID) -> CandidateApplication:
    app = (
        db.query(CandidateApplication)
        .options(
            joinedload(CandidateApplication.current_stage_rel),
            joinedload(CandidateApplication.offer),
            joinedload(CandidateApplication.placement),
        )
        .filter(CandidateApplication.id == app_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return app


def _assert_can_manage_application(
    db: Session,
    app: CandidateApplication,
    current_user: User,
    *,
    require_write: bool = True,
) -> JobRequirement:
    jr = (
        db.query(JobRequirement)
        .options(joinedload(JobRequirement.client), joinedload(JobRequirement.assignee))
        .filter(JobRequirement.id == app.job_requirement_id)
        .first()
    )
    if not jr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job requirement not found")

    role = normalize_role(current_user.role.name)
    if role == ROLE_OWNER:
        return jr

    if role != ROLE_RECRUITER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    recruiter = current_user.recruiter or (
        db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    )
    is_job_assignee = jr.assigned_to == current_user.id
    is_app_recruiter = bool(
        recruiter and app.assigned_recruiter_id and app.assigned_recruiter_id == recruiter.id
    )
    if not (is_job_assignee or is_app_recruiter):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage candidates on your assigned jobs",
        )
    if require_write and not is_job_assignee and not is_app_recruiter:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return jr


def _recruiter_name(db: Session, recruiter_id: uuid.UUID | None) -> str | None:
    if not recruiter_id:
        return None
    rec = (
        db.query(Recruiter)
        .options(joinedload(Recruiter.user))
        .filter(Recruiter.id == recruiter_id)
        .first()
    )
    if not rec or not rec.user:
        return None
    return f"{rec.user.first_name} {rec.user.last_name}".strip()


def serialize_pipeline_card(
    db: Session,
    app: CandidateApplication,
    jr: JobRequirement,
    candidate: Candidate | None,
) -> dict:
    assignee_name = None
    if jr.assignee:
        assignee_name = f"{jr.assignee.first_name} {jr.assignee.last_name}".strip()

    exp = None
    if candidate and candidate.total_experience_years is not None:
        exp = float(candidate.total_experience_years)

    offer_ctc = app.offer.offered_ctc if app.offer else None
    offer_joining = app.offer.joining_date if app.offer else None
    joined = app.placement.joined_date if app.placement else None

    return {
        "id": app.id,
        "candidate_id": app.candidate_id,
        "candidate_name": (
            f"{candidate.first_name} {candidate.last_name}".strip() if candidate else ""
        ),
        "candidate_email": candidate.email if candidate else "",
        "candidate_phone": candidate.phone if candidate else None,
        "current_designation": candidate.current_designation if candidate else None,
        "current_company": candidate.current_company if candidate else None,
        "total_experience_years": exp,
        "job_requirement_id": jr.id,
        "job_title": jr.job_title,
        "client_id": jr.client_id,
        "client_name": jr.client.company_name if jr.client else "",
        "assigned_recruiter_id": app.assigned_recruiter_id,
        "assigned_recruiter_name": _recruiter_name(db, app.assigned_recruiter_id),
        "job_assignee_user_id": jr.assigned_to,
        "job_assignee_name": assignee_name,
        "current_stage_id": app.current_stage,
        "current_stage": app.current_stage_rel.name if app.current_stage_rel else None,
        "status": app.status,
        "owner_status": app.owner_status,
        "applied_date": app.applied_date,
        "submitted_at": app.submitted_at,
        "remarks": None,
        "offer_ctc": offer_ctc,
        "offer_joining_date": offer_joining,
        "joined_date": joined,
    }


def get_pipeline_board(
    db: Session,
    current_user: User,
    *,
    client_id: uuid.UUID | None = None,
    job_requirement_id: uuid.UUID | None = None,
    search: str | None = None,
) -> dict:
    stages = list_pipeline_stages(db)
    stage_ids = [s.id for s in stages]

    query = (
        db.query(CandidateApplication)
        .options(
            joinedload(CandidateApplication.current_stage_rel),
            joinedload(CandidateApplication.offer),
            joinedload(CandidateApplication.placement),
        )
        .filter(CandidateApplication.current_stage.in_(stage_ids))
        .filter(CandidateApplication.owner_status == "approved")
    )

    role = normalize_role(current_user.role.name)
    if role == ROLE_RECRUITER:
        query = query.join(
            JobRequirement,
            CandidateApplication.job_requirement_id == JobRequirement.id,
        ).filter(JobRequirement.assigned_to == current_user.id)
    elif role != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if job_requirement_id:
        query = query.filter(CandidateApplication.job_requirement_id == job_requirement_id)

    apps = query.order_by(CandidateApplication.submitted_at.desc().nullslast()).all()

    jr_ids = {a.job_requirement_id for a in apps}
    cand_ids = {a.candidate_id for a in apps}

    jrs = {
        jr.id: jr
        for jr in db.query(JobRequirement)
        .options(joinedload(JobRequirement.client), joinedload(JobRequirement.assignee))
        .filter(JobRequirement.id.in_(jr_ids))
        .all()
    } if jr_ids else {}

    candidates = {
        c.id: c
        for c in db.query(Candidate).filter(Candidate.id.in_(cand_ids)).all()
    } if cand_ids else {}

    if client_id:
        apps = [a for a in apps if jrs.get(a.job_requirement_id) and jrs[a.job_requirement_id].client_id == client_id]

    q = (search or "").strip().lower()
    cards = []
    for app in apps:
        jr = jrs.get(app.job_requirement_id)
        candidate = candidates.get(app.candidate_id)
        if not jr:
            continue
        card = serialize_pipeline_card(db, app, jr, candidate)
        if q:
            hay = " ".join(
                filter(
                    None,
                    [
                        card["candidate_name"],
                        card["candidate_email"],
                        card["job_title"],
                        card["client_name"],
                        card["current_company"],
                        card["current_designation"],
                    ],
                )
            ).lower()
            if q not in hay:
                continue
        cards.append(card)

    return {
        "stages": [{"id": s.id, "name": s.name, "order_no": s.order_no} for s in stages],
        "cards": cards,
    }


def _record_history(
    db: Session,
    app: CandidateApplication,
    stage: PipelineStage,
    moved_by: uuid.UUID,
    remarks: str | None,
) -> None:
    db.add(
        ApplicationStageHistory(
            application_id=app.id,
            stage_id=stage.id,
            moved_by=moved_by,
            remarks=remarks,
        )
    )


def shortlist_applications(
    db: Session,
    application_ids: list[uuid.UUID],
    current_user: User,
    remarks: str | None = None,
) -> list[dict]:
    if normalize_role(current_user.role.name) != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can shortlist")

    shortlisted = _get_stage_by_name(db, STAGE_SHORTLISTED)
    results: list[dict] = []

    for app_id in application_ids:
        app = _load_app_for_pipeline(db, app_id)
        jr = _assert_can_manage_application(db, app, current_user)

        if app.owner_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Application must be approved before shortlisting ({app_id})",
            )

        current_name = app.current_stage_rel.name if app.current_stage_rel else "Applied"
        if current_name in BOARD_STAGE_NAMES and current_name != "Applied":
            # Already in pipeline — keep stage, ensure active
            app.status = "active"
        else:
            app.current_stage = shortlisted.id
            app.status = "active"
            _record_history(
                db,
                app,
                shortlisted,
                current_user.id,
                remarks or "Shortlisted after client feedback",
            )

        candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()
        db.flush()
        app = _load_app_for_pipeline(db, app.id)
        results.append(serialize_pipeline_card(db, app, jr, candidate))

    db.commit()
    return results


def move_application_stage(
    db: Session,
    app_id: uuid.UUID,
    stage_name: str,
    current_user: User,
    *,
    remarks: str | None = None,
    offered_ctc: Decimal | None = None,
    joining_date: date | None = None,
    joined_date: date | None = None,
    revenue_generated: Decimal | None = None,
) -> dict:
    app = _load_app_for_pipeline(db, app_id)
    jr = _assert_can_manage_application(db, app, current_user)

    if app.owner_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only approved applications can move in the hiring pipeline",
        )

    target = _get_stage_by_name(db, stage_name)
    if target.name not in BOARD_STAGE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot move to stage '{stage_name}' from the pipeline board",
        )

    current_name = app.current_stage_rel.name if app.current_stage_rel else "Applied"
    role = normalize_role(current_user.role.name)

    if current_name == target.name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Candidate is already in this stage",
        )

    if role not in (ROLE_OWNER, ROLE_RECRUITER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if current_name == "Applied":
        if role != ROLE_OWNER or target.name != STAGE_SHORTLISTED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Owner must shortlist this candidate into the pipeline first",
            )
    else:
        allowed = allowed_stage_targets(current_name)
        if target.name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot move from {current_name} to {target.name} (backward moves are not allowed)",
            )

    app.current_stage = target.id
    if target.name == STAGE_REJECTED:
        app.status = "rejected"
    elif target.name == STAGE_ON_HOLD:
        app.status = "on_hold"
    elif target.name == STAGE_JOINED:
        app.status = "joined"
    else:
        app.status = "active"

    if target.name == STAGE_OFFER:
        if not app.offer:
            offer = Offer(
                application_id=app.id,
                offered_ctc=offered_ctc,
                joining_date=joining_date,
                offer_date=date.today(),
                status="pending",
            )
            db.add(offer)
        else:
            if offered_ctc is not None:
                app.offer.offered_ctc = offered_ctc
            if joining_date is not None:
                app.offer.joining_date = joining_date
            app.offer.status = "pending"
            if app.offer.offer_date is None:
                app.offer.offer_date = date.today()

    if target.name == STAGE_JOINED:
        if app.offer:
            app.offer.status = "accepted"
            if joining_date is not None:
                app.offer.joining_date = joining_date
        join_on = joined_date or joining_date or date.today()
        if not app.placement:
            placement = Placement(
                application_id=app.id,
                candidate_id=app.candidate_id,
                client_id=jr.client_id,
                joined_date=join_on,
                revenue_generated=revenue_generated,
                invoice_status="pending",
            )
            db.add(placement)
        else:
            app.placement.joined_date = join_on
            if revenue_generated is not None:
                app.placement.revenue_generated = revenue_generated

        # Placed candidates leave the active talent pool.
        candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()
        if candidate:
            candidate.candidate_status = "inactive"

    _record_history(db, app, target, current_user.id, remarks)
    db.commit()

    app = _load_app_for_pipeline(db, app.id)
    jr = (
        db.query(JobRequirement)
        .options(joinedload(JobRequirement.client), joinedload(JobRequirement.assignee))
        .filter(JobRequirement.id == app.job_requirement_id)
        .one()
    )
    candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()
    return serialize_pipeline_card(db, app, jr, candidate)


def get_stage_history(db: Session, app_id: uuid.UUID, current_user: User) -> list[dict]:
    app = _load_app_for_pipeline(db, app_id)
    _assert_can_manage_application(db, app, current_user, require_write=False)

    rows = (
        db.query(ApplicationStageHistory)
        .options(joinedload(ApplicationStageHistory.stage))
        .filter(ApplicationStageHistory.application_id == app_id)
        .order_by(ApplicationStageHistory.created_at.asc())
        .all()
    )
    user_ids = {r.moved_by for r in rows}
    users = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}

    result = []
    for row in rows:
        mover = users.get(row.moved_by)
        result.append(
            {
                "id": row.id,
                "stage_id": row.stage_id,
                "stage_name": row.stage.name if row.stage else "",
                "moved_by": row.moved_by,
                "moved_by_name": (
                    f"{mover.first_name} {mover.last_name}".strip() if mover else None
                ),
                "remarks": row.remarks,
                "created_at": row.created_at,
            }
        )
    return result


def get_candidate_stage_history(
    db: Session,
    candidate_id: uuid.UUID,
    current_user: User,
) -> dict:
    """Return ApplicationStageHistory for all applications of a candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    query = (
        db.query(CandidateApplication)
        .options(
            joinedload(CandidateApplication.current_stage_rel),
            joinedload(CandidateApplication.stage_history).joinedload(
                ApplicationStageHistory.stage
            ),
        )
        .filter(CandidateApplication.candidate_id == candidate_id)
    )

    role = normalize_role(current_user.role.name)
    if role == ROLE_RECRUITER:
        query = query.join(
            JobRequirement,
            CandidateApplication.job_requirement_id == JobRequirement.id,
        ).filter(JobRequirement.assigned_to == current_user.id)
    elif role != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    apps = query.order_by(CandidateApplication.submitted_at.desc().nullslast()).all()

    jr_ids = {a.job_requirement_id for a in apps}
    jrs = {
        jr.id: jr
        for jr in db.query(JobRequirement)
        .options(joinedload(JobRequirement.client))
        .filter(JobRequirement.id.in_(jr_ids))
        .all()
    } if jr_ids else {}

    mover_ids: set[uuid.UUID] = set()
    for app in apps:
        for row in app.stage_history:
            mover_ids.add(row.moved_by)
    movers = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(mover_ids)).all()
    } if mover_ids else {}

    applications: list[dict] = []
    for app in apps:
        jr = jrs.get(app.job_requirement_id)
        if not jr:
            continue
        history_rows = sorted(app.stage_history, key=lambda r: r.created_at)
        applications.append(
            {
                "application_id": app.id,
                "job_requirement_id": jr.id,
                "job_title": jr.job_title,
                "client_id": jr.client_id,
                "client_name": jr.client.company_name if jr.client else "",
                "current_stage": app.current_stage_rel.name if app.current_stage_rel else None,
                "owner_status": app.owner_status,
                "status": app.status,
                "submitted_at": app.submitted_at,
                "history": [
                    {
                        "id": row.id,
                        "stage_id": row.stage_id,
                        "stage_name": row.stage.name if row.stage else "",
                        "moved_by": row.moved_by,
                        "moved_by_name": (
                            f"{movers[row.moved_by].first_name} {movers[row.moved_by].last_name}".strip()
                            if movers.get(row.moved_by)
                            else None
                        ),
                        "remarks": row.remarks,
                        "created_at": row.created_at,
                    }
                    for row in history_rows
                ],
            }
        )

    return {"candidate_id": candidate_id, "applications": applications}


def share_approved_with_client(
    db: Session,
    client_id: uuid.UUID,
    current_user: User,
    *,
    to_emails: list[str] | None = None,
    subject: str | None = None,
    message: str | None = None,
    application_ids: list[uuid.UUID] | None = None,
) -> dict:
    if normalize_role(current_user.role.name) != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can share")

    from app.services.submission_service import generate_bulk_approved_client_excel

    client = (
        db.query(Client)
        .options(joinedload(Client.contacts))
        .filter(Client.id == client_id)
        .first()
    )
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    recipients = [e.strip() for e in (to_emails or []) if e and e.strip()]
    if not recipients:
        recipients = [
            c.email.strip()
            for c in client.contacts
            if c.email and c.email.strip()
        ]
    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No client contact emails found. Add contacts or provide to_emails.",
        )

    # Reuse Excel generator; optionally filter would need extension — for now share all approved.
    # If application_ids provided, still generate full approved sheet (simpler) but count filter.
    excel_bytes, filename = generate_bulk_approved_client_excel(db, client_id, current_user)

    # Count approved for this client (optionally filtered)
    approved_q = (
        db.query(CandidateApplication)
        .join(JobRequirement, CandidateApplication.job_requirement_id == JobRequirement.id)
        .filter(JobRequirement.client_id == client_id)
        .filter(CandidateApplication.owner_status == "approved")
    )
    if application_ids:
        approved_q = approved_q.filter(CandidateApplication.id.in_(application_ids))
    count = approved_q.count()
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No approved candidates to share for this client",
        )

    company = settings.COMPANY_NAME
    mail_subject = subject or f"{company} — Candidate profiles for {client.company_name}"
    body = message or (
        f"Dear {client.company_name} team,\n\n"
        f"Please find attached {count} approved candidate profile(s) from {company} "
        f"for your review.\n\n"
        f"Kindly share your shortlisted candidates so we can proceed with the hiring pipeline.\n\n"
        f"Regards,\n{company} Talent Team"
    )

    result = send_email_with_attachment(
        to_emails=recipients,
        subject=mail_subject,
        body_text=body,
        attachment_bytes=excel_bytes,
        attachment_filename=filename,
    )
    return {
        **result,
        "candidate_count": count,
    }


def get_email_status() -> dict:
    return {"configured": email_configured()}
