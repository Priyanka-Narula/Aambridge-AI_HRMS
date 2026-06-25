import logging
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.schemas.cv import CandidateDraft
from app.models.candidate import (
    Candidate,
    CandidateSkill,
    Education,
    Skill,
    WorkExperience,
)
from app.services.data_cleaner import clean_candidate_data

logger = logging.getLogger(__name__)


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

    candidate = Candidate(
        first_name=draft.first_name,
        last_name=draft.last_name,
        email=str(draft.email),
        nationality=draft.nationality,
        date_of_birth=draft.date_of_birth,
        languages_known=draft.languages_known,
        phone=draft.phone,
        visa_status=draft.visa_status,
        linkedin_url=draft.linkedin_url,
        current_location=draft.current_location,
        preferred_location=draft.preferred_location,
        total_experience_years=draft.total_experience_years,
        current_company=draft.current_company,
        current_designation=draft.current_designation,
        current_ctc=draft.current_ctc,
        expected_ctc=draft.expected_ctc,
        notice_period=draft.notice_period,
        resume_url=draft.resume_url,
        source=draft.source,
        candidate_status=draft.candidate_status or "active",
        created_by=created_by,
    )
    db.add(candidate)
    db.flush()

    for skill_draft in draft.skills:
        skill = db.query(Skill).filter(Skill.name == skill_draft.name).first()
        if not skill:
            skill = Skill(name=skill_draft.name)
            db.add(skill)
            db.flush()
        db.add(
            CandidateSkill(
                candidate_id=candidate.id,
                skill_id=skill.id,
                years_experience=skill_draft.years_experience,
                proficiency_level=skill_draft.proficiency_level,
            )
        )

    for edu_draft in draft.education:
        db.add(
            Education(
                candidate_id=candidate.id,
                degree=edu_draft.degree,
                specialization=edu_draft.specialization,
                institution=edu_draft.institution,
                start_year=edu_draft.start_year,
                end_year=edu_draft.end_year,
                percentage=edu_draft.percentage,
            )
        )

    for exp_draft in draft.work_experience:
        db.add(
            WorkExperience(
                candidate_id=candidate.id,
                company_name=exp_draft.company_name,
                designation=exp_draft.designation,
                start_date=exp_draft.start_date,
                end_date=exp_draft.end_date,
                currently_working=exp_draft.currently_working,
                job_description=exp_draft.job_description,
            )
        )

    db.commit()
    db.refresh(candidate)
    logger.info("Saved candidate %s (%s)", candidate.id, candidate.email)
    return candidate
