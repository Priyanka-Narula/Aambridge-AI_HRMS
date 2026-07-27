from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_applications.id"), unique=True, nullable=False
    )
    offered_ctc: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    joining_date: Mapped[date | None] = mapped_column(Date)
    offer_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    application: Mapped["CandidateApplication"] = relationship(back_populates="offer")


class Placement(Base):
    __tablename__ = "placements"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_applications.id"), unique=True, nullable=False
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    joined_date: Mapped[date | None] = mapped_column(Date, index=True)
    revenue_generated: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    invoice_status: Mapped[str | None] = mapped_column(String(50))

    application: Mapped["CandidateApplication"] = relationship(back_populates="placement")
