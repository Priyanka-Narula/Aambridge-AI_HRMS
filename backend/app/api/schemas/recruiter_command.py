from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.api.schemas.command_center import (
    BusinessTrend,
    ExecutiveKpi,
    HiringFunnel,
    OpenJobRow,
    RecruiterLeaderboardRow,
)


class RecruiterFocusItem(BaseModel):
    key: str
    label: str
    value: int = 0
    tone: Literal["neutral", "attention", "urgent", "positive"] = "neutral"
    action_href: str


class RecruiterActionItem(BaseModel):
    key: str
    priority: Literal["high", "medium", "low"]
    title: str
    description: str
    count: int = 0
    action_label: str
    action_href: str


class RecruiterStanding(BaseModel):
    rank: int | None = None
    total_recruiters: int = 0
    team_median_score: float = 0
    me: RecruiterLeaderboardRow | None = None
    peers: list[RecruiterLeaderboardRow] = Field(default_factory=list)


class RecruiterCommandResponse(BaseModel):
    today_focus: list[RecruiterFocusItem] = Field(default_factory=list)
    kpis: list[ExecutiveKpi] = Field(default_factory=list)
    standing: RecruiterStanding
    hiring_funnel: HiringFunnel
    action_queue: list[RecruiterActionItem] = Field(default_factory=list)
    job_health: list[OpenJobRow] = Field(default_factory=list)
    personal_trend: BusinessTrend
