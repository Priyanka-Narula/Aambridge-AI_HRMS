import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = uuid_pk()
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(100))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    languages_known: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    visa_status: Mapped[str | None] = mapped_column(String(100))
    linkedin_url: Mapped[str | None] = mapped_column(String(255))
    current_location: Mapped[str | None] = mapped_column(String(255))
    preferred_location: Mapped[str | None] = mapped_column(String(255))
    total_experience_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    current_company: Mapped[str | None] = mapped_column(String(255))
    current_designation: Mapped[str | None] = mapped_column(String(100))
    current_ctc: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    expected_ctc: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    notice_period: Mapped[str | None] = mapped_column(String(50))
    resume_url: Mapped[str | None] = mapped_column(String(500))
    candidate_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )
    source: Mapped[str | None] = mapped_column(String(100))
    created_by: Mapped[str | None] = mapped_column(String(255), index=True)
    uae_experience_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    industry: Mapped[str | None] = mapped_column(String(100))

    skills: Mapped[list["CandidateSkill"]] = relationship(back_populates="candidate")
    education_records: Mapped[list["Education"]] = relationship(back_populates="candidate")
    work_experiences: Mapped[list["WorkExperience"]] = relationship(
        back_populates="candidate"
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    candidate_skills: Mapped[list["CandidateSkill"]] = relationship(
        back_populates="skill"
    )


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False
    )
    years_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    proficiency_level: Mapped[str | None] = mapped_column(String(50))
    candidate_summary: Mapped[str | None] = mapped_column(String(500))

    candidate: Mapped["Candidate"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="candidate_skills")


class Education(Base):
    __tablename__ = "education"

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    degree: Mapped[str] = mapped_column(String(100), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(100))
    institution: Mapped[str | None] = mapped_column(String(255))
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    candidate: Mapped["Candidate"] = relationship(back_populates="education_records")


class WorkExperience(Base):
    __tablename__ = "work_experience"

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    currently_working: Mapped[bool] = mapped_column(default=False, nullable=False)
    job_description: Mapped[str | None] = mapped_column(Text)

    candidate: Mapped["Candidate"] = relationship(back_populates="work_experiences")
