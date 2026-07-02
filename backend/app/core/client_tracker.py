from __future__ import annotations

import asyncio


class ClientTracker:
    """Track the number of connected WebSocket clients.

    Used by the poller to switch between active (fast) and idle (slow) refresh
    cadences depending on whether any browser tab is viewing the dashboard.
    """

    def __init__(self) -> None:
        self._count = 0
        self._lock = asyncio.Lock()

    async def add(self) -> bool:
        """Register a new client.  Returns True if this was the first client."""
        async with self._lock:
            was_zero = self._count == 0
            self._count += 1
            return was_zero

    async def remove(self) -> bool:
        """Unregister a client.  Returns True if the last client just left."""
        async with self._lock:
            self._count = max(0, self._count - 1)
            return self._count == 0

    @property
    def active(self) -> bool:
        return self._count > 0

    @property
    def count(self) -> int:
        return self._count


client_tracker = ClientTracker()
