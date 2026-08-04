from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.command_center import CommandCenterResponse
from app.api.schemas.dashboard import (
    AnalyticsDashboardResponse,
    DashboardNotificationsResponse,
    RecruiterPerformanceResponse,
    DashboardStatsResponse,
)
from app.core.database import SessionLocal, get_db
from app.core.deps import get_current_user
from app.core.security import ROLE_OWNER, decode_access_token, normalize_role
from app.models.user_access import User
from app.services import command_center_service, dashboard_service
from app.services.dashboard_events import dashboard_hub

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/analytics", response_model=AnalyticsDashboardResponse)
def analytics_dashboard(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dashboard_service.get_analytics_dashboard(
        db,
        current_user,
        start=start,
        end=end,
    )


@router.get("/recruiter-performance", response_model=RecruiterPerformanceResponse)
def recruiter_performance(
    period: Literal["monthly", "till_date"] = Query(default="monthly"),
    industry: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if normalize_role(current_user.role.name) != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return dashboard_service.get_recruiter_performance(
        db,
        period=period,
        industry=industry,
    )


@router.get("/command-center", response_model=CommandCenterResponse)
def command_center(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    trend_grain: Literal["weekly", "monthly", "quarterly", "yearly"] = Query(default="monthly"),
    recruiter_id: UUID | None = Query(default=None),
    client_id: UUID | None = Query(default=None),
    department: str | None = Query(default=None),
    job_status: str | None = Query(default=None),
    location: str | None = Query(default=None),
    activity_limit: int = Query(default=5, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return command_center_service.get_command_center(
        db,
        current_user,
        start=start,
        end=end,
        trend_grain=trend_grain,
        recruiter_id=recruiter_id,
        client_id=client_id,
        department=department,
        job_status=job_status,
        location=location,
        activity_limit=activity_limit,
    )


@router.get("/notifications", response_model=DashboardNotificationsResponse)
def dashboard_notifications(
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dashboard_service.get_dashboard_notifications(db, current_user, limit=limit)


@router.get("/stats", response_model=DashboardStatsResponse)
def dashboard_stats(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compact legacy stats used by earlier dashboard widgets."""
    full = dashboard_service.get_analytics_dashboard(
        db,
        current_user,
        start=start,
        end=end,
    )
    kpis = full["kpis"]
    return {
        "open_jobs": kpis.get("open_jobs", 0),
        "closed_jobs": kpis.get("closed_jobs", 0),
        "active_candidates": kpis.get("active_candidates", 0),
        "submissions_total": (
            kpis.get("submissions_pending", 0)
            + kpis.get("submissions_approved", 0)
            + kpis.get("submissions_rejected", 0)
        ),
        "submissions_pending": kpis.get("submissions_pending", 0),
        "submissions_approved": kpis.get("submissions_approved", 0),
        "in_pipeline": kpis.get("in_pipeline", 0),
        "interviews_scheduled": kpis.get("interviews_scheduled", 0),
        "offers_pending": kpis.get("offers", 0),
        "joined": kpis.get("placements", 0),
        "pipeline_stages": full["charts"].get("pipeline_stages", []),
    }


@router.websocket("/ws")
async def dashboard_ws(websocket: WebSocket, token: str | None = None):
    if not token:
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=4401)
                return
            user = (
                db.query(User)
                .options(joinedload(User.role))
                .filter(User.id == UUID(user_id))
                .first()
            )
            if not user or user.status != "active":
                await websocket.close(code=4401)
                return
        except (JWTError, ValueError):
            await websocket.close(code=4401)
            return

        uid = str(user.id)
        await dashboard_hub.connect(uid, websocket)
        try:
            await websocket.send_json({"type": "connected", "widgets": []})
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                # Ignore client keep-alive pings / text frames.
        except WebSocketDisconnect:
            pass
        finally:
            await dashboard_hub.disconnect(uid, websocket)
    finally:
        db.close()
