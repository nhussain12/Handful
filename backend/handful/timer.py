from __future__ import annotations

import asyncio
import time
import uuid

from .models import TimerData


class TimerManager:
    def __init__(self) -> None:
        self._timers: dict[str, TimerData] = {}
        self._lock = asyncio.Lock()
        self._on_timer_finished: callable | None = None

    def set_on_timer_finished(self, callback: callable) -> None:
        self._on_timer_finished = callback

    async def start_timer(self, minutes: float, label: str) -> dict:
        timer_id = uuid.uuid4().hex[:8]
        duration = minutes * 60.0
        now = time.time()

        timer = TimerData(
            id=timer_id,
            label=label,
            duration_seconds=duration,
            remaining_seconds=duration,
            is_running=True,
            created_at=now,
        )

        async with self._lock:
            self._timers[timer_id] = timer

        asyncio.create_task(self._run_timer(timer_id, duration))

        return {
            "success": True,
            "timer_id": timer_id,
            "label": label,
            "minutes": minutes,
        }

    async def _run_timer(self, timer_id: str, duration: float) -> None:
        try:
            await asyncio.sleep(duration)
        except asyncio.CancelledError:
            return

        async with self._lock:
            if timer_id in self._timers:
                self._timers[timer_id].is_running = False
                self._timers[timer_id].is_expired = True
                self._timers[timer_id].remaining_seconds = 0.0
                label = self._timers[timer_id].label

        if self._on_timer_finished:
            await self._on_timer_finished(timer_id, label)

    async def cancel_timer(self, label: str) -> dict:
        async with self._lock:
            for tid, timer in list(self._timers.items()):
                if timer.label.lower() == label.lower() and timer.is_running:
                    timer.is_running = False
                    timer.is_expired = True
                    timer.remaining_seconds = 0.0
                    return {
                        "success": True,
                        "timer_id": tid,
                        "label": label,
                    }
        return {"success": False, "error": f"No running timer found with label '{label}'"}

    async def get_timers(self) -> dict:
        now = time.time()
        async with self._lock:
            for timer in self._timers.values():
                if timer.is_running and not timer.is_expired:
                    elapsed = now - timer.created_at
                    timer.remaining_seconds = max(0.0, timer.duration_seconds - elapsed)

            all_timers = [t.to_dict() for t in self._timers.values()]

        return {"success": True, "timers": all_timers, "count": len(all_timers)}

    def get_active_timers(self) -> list[dict]:
        now = time.time()
        updates = []
        for timer in list(self._timers.values()):
            if timer.is_running and not timer.is_expired:
                elapsed = now - timer.created_at
                timer.remaining_seconds = max(0.0, timer.duration_seconds - elapsed)
                updates.append(timer.to_dict())
        return updates
