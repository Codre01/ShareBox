from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class EventBus:
    """Simple in-process pub/sub for SSE file-change notifications."""

    def __init__(self) -> None:
        self._subscribers: dict[int, asyncio.Queue[dict[str, Any]]] = {}
        self._next_id = 0
        self._lock = asyncio.Lock()

    async def subscribe(self) -> tuple[int, asyncio.Queue[dict[str, Any]]]:
        async with self._lock:
            self._next_id += 1
            q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
            self._subscribers[self._next_id] = q
            return self._next_id, q

    async def unsubscribe(self, sub_id: int) -> None:
        async with self._lock:
            self._subscribers.pop(sub_id, None)

    async def publish(self, event: dict[str, Any]) -> None:
        async with self._lock:
            dead: list[int] = []
            for sid, q in self._subscribers.items():
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead.append(sid)
            for sid in dead:
                self._subscribers.pop(sid, None)


# Shared module-level bus used by filesystem watcher and SSE endpoint.
bus = EventBus()
