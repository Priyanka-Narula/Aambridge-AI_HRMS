"""In-memory WebSocket hub for dashboard live updates."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

_main_loop: asyncio.AbstractEventLoop | None = None


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Capture the app event loop so sync route handlers can publish events."""
    global _main_loop
    _main_loop = loop


class DashboardEventHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        stale: list[WebSocket] = []
        async with self._lock:
            existing = self._connections.setdefault(user_id, set())
            # Keep a single live socket per user to avoid Windows socket exhaustion.
            for old in list(existing):
                if old is not websocket:
                    stale.append(old)
                    existing.discard(old)
            existing.add(websocket)
        for old in stale:
            try:
                await old.close(code=1000)
            except Exception:
                logger.debug("Failed closing replaced dashboard websocket for %s", user_id)

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
WIDGETS_CLIENT = [
    "kpis",
    "client_placements",
    "recent_activities",
    "notifications",
]


def publish_dashboard_event(event_type: str, widgets: list[str], detail: dict[str, Any] | None = None) -> None:
    """Broadcast from sync or async service code (thread-pool safe)."""
    payload = {
        "type": event_type,
        "widgets": widgets,
        "detail": detail or {},
    }
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = _main_loop

    if loop is None or not loop.is_running():
        logger.debug("Skipping dashboard event %s — no running event loop", event_type)
        return

    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None

    if running is loop:
        loop.create_task(dashboard_hub.broadcast(payload))
    else:
        asyncio.run_coroutine_threadsafe(dashboard_hub.broadcast(payload), loop)
