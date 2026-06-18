import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)

    applications: Mapped[list["CandidateApplication"]] = relationship(
        back_populates="current_stage_rel"
    )
    stage_history: Mapped[list["ApplicationStageHistory"]] = relationship(
        back_populates="stage"
    )


class CandidateApplication(Base):
    __tablename__ = "candidate_applications"

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    job_requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_requirements.id"), nullable=False
    )
    assigned_recruiter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recruiters.id")
    )
    current_stage: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipeline_stages.id")
    )
    applied_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    current_stage_rel: Mapped["PipelineStage | None"] = relationship(
        back_populates="applications"
    )
    stage_history: Mapped[list["ApplicationStageHistory"]] = relationship(
        back_populates="application"
    )
    interviews: Mapped[list["Interview"]] = relationship(back_populates="application")
    offer: Mapped["Offer | None"] = relationship(
        back_populates="application", uselist=False
    )
    placement: Mapped["Placement | None"] = relationship(
        back_populates="application", uselist=False
    )


class ApplicationStageHistory(Base):
    __tablename__ = "application_stage_history"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_applications.id"), nullable=False
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=False
    )
    moved_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped["CandidateApplication"] = relationship(
        back_populates="stage_history"
    )
    stage: Mapped["PipelineStage"] = relationship(back_populates="stage_history")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_applications.id"), nullable=False
    )
    interview_round: Mapped[int] = mapped_column(Integer, nullable=False)
    interviewer_name: Mapped[str | None] = mapped_column(String(255))
    scheduled_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mode: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="scheduled")
    feedback: Mapped[str | None] = mapped_column(Text)

    application: Mapped["CandidateApplication"] = relationship(back_populates="interviews")
    feedback_detail: Mapped["InterviewFeedback | None"] = relationship(
        back_populates="interview", uselist=False
    )


class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"

    id: Mapped[uuid.UUID] = uuid_pk()
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id"), unique=True, nullable=False
    )
    technical_rating: Mapped[int | None] = mapped_column(Integer)
    communication_rating: Mapped[int | None] = mapped_column(Integer)
    culture_rating: Mapped[int | None] = mapped_column(Integer)
    overall_rating: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[str | None] = mapped_column(Text)

    interview: Mapped["Interview"] = relationship(back_populates="feedback_detail")
