import logging
import uuid
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.candidate import CandidateCreate, CandidateUpdate
from app.api.schemas.cv import CandidateDraft
from app.models.candidate import (
    Candidate,
    CandidateSkill,
    Education,
    Skill,
    WorkExperience,
)
from app.models.offer import Offer, Placement
from app.models.pipeline import (
    ApplicationStageHistory,
    CandidateApplication,
    Interview,
    InterviewFeedback,
)
from app.services.data_cleaner import clean_candidate_data

logger = logging.getLogger(__name__)


def _candidate_query(db: Session):
    return db.query(Candidate).options(
        joinedload(Candidate.skills).joinedload(CandidateSkill.skill),
        joinedload(Candidate.education_records),
        joinedload(Candidate.work_experiences),
    )


def get_candidate_or_404(db: Session, candidate_id: uuid.UUID) -> Candidate:
    candidate = _candidate_query(db).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


def list_candidates(db: Session) -> list[Candidate]:
    return _candidate_query(db).order_by(Candidate.created_at.desc()).all()


def _get_or_create_skill(db: Session, name: str) -> Skill:
    skill = db.query(Skill).filter(Skill.name == name).first()
    if not skill:
        skill = Skill(name=name)
        db.add(skill)
        db.flush()
    return skill


def _to_mapping(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    raise TypeError(f"Unsupported relation payload type: {type(item)!r}")


def _apply_skills(db: Session, candidate: Candidate, skills: list) -> None:
    db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate.id).delete()
    db.flush()
    for skill_input in skills:
        data = _to_mapping(skill_input)
        name = str(data.get("name") or "").strip()
        if not name:
            continue
        skill = _get_or_create_skill(db, name)
        db.add(
            CandidateSkill(
                candidate_id=candidate.id,
                skill_id=skill.id,
                years_experience=data.get("years_experience"),
                proficiency_level=data.get("proficiency_level"),
            )
        )


def _apply_education(db: Session, candidate: Candidate, records: list) -> None:
    db.query(Education).filter(Education.candidate_id == candidate.id).delete()
    db.flush()
    for edu in records:
        data = _to_mapping(edu)
        degree = str(data.get("degree") or "").strip()
        if not degree:
            continue
        db.add(
            Education(
                candidate_id=candidate.id,
                degree=degree,
                specialization=data.get("specialization"),
                institution=data.get("institution"),
                start_year=data.get("start_year"),
                end_year=data.get("end_year"),
                percentage=data.get("percentage"),
            )
        )


def _apply_work_experience(db: Session, candidate: Candidate, experiences: list) -> None:
    db.query(WorkExperience).filter(WorkExperience.candidate_id == candidate.id).delete()
    db.flush()
    for exp in experiences:
        data = _to_mapping(exp)
        company = str(data.get("company_name") or "").strip()
        if not company:
            continue
        db.add(
            WorkExperience(
                candidate_id=candidate.id,
                company_name=company,
                designation=data.get("designation"),
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                currently_working=bool(data.get("currently_working", False)),
                job_description=data.get("job_description"),
            )
        )


def _check_duplicate_email(db: Session, email: str, exclude_id: uuid.UUID | None = None) -> None:
    query = db.query(Candidate).filter(Candidate.email == email)
    if exclude_id:
        query = query.filter(Candidate.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Candidate with this email already exists")


def create_candidate_record(db: Session, payload: CandidateCreate) -> Candidate:
    _check_duplicate_email(db, str(payload.email))
    data = payload.model_dump(exclude={"skills", "education_records", "work_experiences"})
    candidate = Candidate(**data)
    db.add(candidate)
    db.flush()
    _apply_skills(db, candidate, payload.skills)
    _apply_education(db, candidate, payload.education_records)
    _apply_work_experience(db, candidate, payload.work_experiences)
    db.commit()
    return get_candidate_or_404(db, candidate.id)


def update_candidate_record(db: Session, candidate_id: uuid.UUID, payload: CandidateUpdate) -> Candidate:
    candidate = get_candidate_or_404(db, candidate_id)
    _check_duplicate_email(db, str(payload.email), exclude_id=candidate_id)
    data = payload.model_dump(exclude={"skills", "education_records", "work_experiences"})
    for key, value in data.items():
        setattr(candidate, key, value)
    _apply_skills(db, candidate, payload.skills)
    _apply_education(db, candidate, payload.education_records)
    _apply_work_experience(db, candidate, payload.work_experiences)
    db.commit()
    return get_candidate_or_404(db, candidate.id)


def delete_candidate_record(db: Session, candidate_id: uuid.UUID) -> None:
    # Avoid eager-loaded relationships: bulk deletes + ORM delete cause StaleDataError.
    exists = db.query(Candidate.id).filter(Candidate.id == candidate_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Candidate not found")

    app_ids = [
        row[0]
        for row in db.query(CandidateApplication.id)
        .filter(CandidateApplication.candidate_id == candidate_id)
        .all()
    ]

    if app_ids:
        interview_ids = [
            row[0]
            for row in db.query(Interview.id).filter(Interview.application_id.in_(app_ids)).all()
        ]
        if interview_ids:
            db.query(InterviewFeedback).filter(
                InterviewFeedback.interview_id.in_(interview_ids)
            ).delete(synchronize_session=False)
            db.query(Interview).filter(Interview.id.in_(interview_ids)).delete(
                synchronize_session=False
            )

        db.query(ApplicationStageHistory).filter(
            ApplicationStageHistory.application_id.in_(app_ids)
        ).delete(synchronize_session=False)
        db.query(Offer).filter(Offer.application_id.in_(app_ids)).delete(
            synchronize_session=False
        )
        db.query(Placement).filter(Placement.application_id.in_(app_ids)).delete(
            synchronize_session=False
        )
        db.query(CandidateApplication).filter(CandidateApplication.id.in_(app_ids)).delete(
            synchronize_session=False
        )

    db.query(Placement).filter(Placement.candidate_id == candidate_id).delete(
        synchronize_session=False
    )
    db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate_id).delete(
        synchronize_session=False
    )
    db.query(Education).filter(Education.candidate_id == candidate_id).delete(
        synchronize_session=False
    )
    db.query(WorkExperience).filter(WorkExperience.candidate_id == candidate_id).delete(
        synchronize_session=False
    )
    db.query(Candidate).filter(Candidate.id == candidate_id).delete(synchronize_session=False)
    db.commit()


def validate_candidate_draft(candidate_data: dict[str, Any]) -> tuple[CandidateDraft | None, list[str]]:
    errors: list[str] = []
    cleaned = clean_candidate_data(candidate_data)
    try:
        draft = CandidateDraft(**cleaned)
    except ValidationError as exc:
        draft = None
        errors.extend(
            f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}" for err in exc.errors()
        )
    return draft, errors


def _draft_to_create(draft: CandidateDraft, created_by: str | None) -> CandidateCreate:
    return CandidateCreate(
        first_name=draft.first_name,
        last_name=draft.last_name,
        email=draft.email,
        nationality=draft.nationality,
        date_of_birth=draft.date_of_birth,
        languages_known=draft.languages_known,
        phone=draft.phone,
        visa_status=draft.visa_status,
        linkedin_url=draft.linkedin_url,
        current_location=draft.current_location,
        preferred_location=draft.preferred_location,
        total_experience_years=draft.total_experience_years,
        uae_experience_years=draft.uae_experience_years,
        industry=draft.industry,
        current_company=draft.current_company,
        current_designation=draft.current_designation,
        current_ctc=draft.current_ctc,
        expected_ctc=draft.expected_ctc,
        notice_period=draft.notice_period,
        resume_url=draft.resume_url,
        source=draft.source,
        candidate_status=draft.candidate_status or "active",
        created_by=created_by,
        skills=[
            {"name": s.name, "years_experience": s.years_experience, "proficiency_level": s.proficiency_level}
            for s in draft.skills
        ],
        education_records=[
            {
                "degree": e.degree,
                "specialization": e.specialization,
                "institution": e.institution,
                "start_year": e.start_year,
                "end_year": e.end_year,
                "percentage": e.percentage,
            }
            for e in draft.education
        ],
        work_experiences=[
            {
                "company_name": w.company_name,
                "designation": w.designation,
                "start_date": w.start_date,
                "end_date": w.end_date,
                "currently_working": w.currently_working,
                "job_description": w.job_description,
            }
            for w in draft.work_experience
        ],
    )


def save_candidate_record(db: Session, draft: CandidateDraft, created_by: str | None) -> Candidate:
    existing = db.query(Candidate).filter(Candidate.email == str(draft.email)).first()
    if not existing and draft.phone:
        existing = (
            db.query(Candidate)
            .filter(
                Candidate.first_name == draft.first_name,
                Candidate.last_name == draft.last_name,
                Candidate.phone == draft.phone,
            )
            .first()
        )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Candidate already exists: {existing.first_name} {existing.last_name} "
                f"(id: {existing.id}, email: {existing.email})."
            ),
        )
    payload = _draft_to_create(draft, created_by)
    candidate = create_candidate_record(db, payload)
    logger.info("Saved candidate %s (%s)", candidate.id, candidate.email)
    return candidate


def serialize_candidate(candidate: Candidate) -> dict[str, Any]:
    return {
        "id": candidate.id,
        "first_name": candidate.first_name,
        "last_name": candidate.last_name,
        "email": candidate.email,
        "nationality": candidate.nationality,
        "date_of_birth": candidate.date_of_birth,
        "languages_known": candidate.languages_known,
        "phone": candidate.phone,
        "visa_status": candidate.visa_status,
        "linkedin_url": candidate.linkedin_url,
        "current_location": candidate.current_location,
        "preferred_location": candidate.preferred_location,
        "total_experience_years": candidate.total_experience_years,
        "uae_experience_years": candidate.uae_experience_years,
        "industry": candidate.industry,
        "current_company": candidate.current_company,
        "current_designation": candidate.current_designation,
        "current_ctc": candidate.current_ctc,
        "expected_ctc": candidate.expected_ctc,
        "notice_period": candidate.notice_period,
        "resume_url": candidate.resume_url,
        "candidate_status": candidate.candidate_status,
        "source": candidate.source,
        "created_by": candidate.created_by,
        "created_at": candidate.created_at,
        "updated_at": candidate.updated_at,
        "skills": [
            {
                "id": cs.id,
                "name": cs.skill.name if cs.skill else "Unknown",
                "years_experience": cs.years_experience,
                "proficiency_level": cs.proficiency_level,
            }
            for cs in candidate.skills
        ],
        "education_records": [
            {
                "id": edu.id,
                "degree": edu.degree,
                "specialization": edu.specialization,
                "institution": edu.institution,
                "start_year": edu.start_year,
                "end_year": edu.end_year,
                "percentage": edu.percentage,
            }
            for edu in candidate.education_records
        ],
        "work_experiences": [
            {
                "id": exp.id,
                "company_name": exp.company_name,
                "designation": exp.designation,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "currently_working": exp.currently_working,
                "job_description": exp.job_description,
            }
            for exp in candidate.work_experiences
        ],
    }
