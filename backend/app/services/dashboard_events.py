"""In-memory WebSocket hub for dashboard live updates."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class DashboardEventHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(user_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(user_id, None)

    async def broadcast(self, payload: dict[str, Any], *, user_ids: list[str] | None = None) -> None:
        async with self._lock:
            if user_ids is None:
                targets = [(uid, set(socks)) for uid, socks in self._connections.items()]
            else:
                targets = [
                    (uid, set(self._connections.get(uid, set())))
                    for uid in user_ids
                    if uid in self._connections
                ]

        stale: list[tuple[str, WebSocket]] = []
        for user_id, sockets in targets:
            for ws in sockets:
                try:
                    await ws.send_json(payload)
                except Exception:
                    logger.debug("Dropping stale dashboard websocket for %s", user_id)
                    stale.append((user_id, ws))

        for user_id, ws in stale:
            await self.disconnect(user_id, ws)


dashboard_hub = DashboardEventHub()


# Widget groups the frontend can selectively refresh.
WIDGETS_CANDIDATE_UPLOAD = [
    "kpis",
    "candidate_status",
    "candidate_uploads_monthly",
    "recent_activities",
    "notifications",
    "recent_candidates",
]
WIDGETS_CANDIDATE_DECISION = [
    "kpis",
    "candidate_status",
    "recruiter_performance",
    "recent_activities",
    "notifications",
    "pending_tasks",
]
WIDGETS_PLACEMENT = [
    "kpis",
    "pipeline_stages",
    "placements_monthly",
    "client_placements",
    "recruiter_performance",
    "recent_placements",
    "recent_activities",
    "notifications",
]
WIDGETS_JOB_CLOSED = [
    "kpis",
    "recent_activities",
    "notifications",
]


def publish_dashboard_event(event_type: str, widgets: list[str], detail: dict[str, Any] | None = None) -> None:
    """Fire-and-forget broadcast from sync service code."""
    payload = {
        "type": event_type,
        "widgets": widgets,
        "detail": detail or {},
    }
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No event loop (e.g. sync script) — skip live push.
        return
    loop.create_task(dashboard_hub.broadcast(payload))
