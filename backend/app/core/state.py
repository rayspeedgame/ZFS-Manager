from __future__ import annotations

import asyncio

from app.schemas.zfs_state import AppState


class StateStore:
    """In-memory state container shared by the API and background poller."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition()
        self._state = AppState()
        self._version = 0

    async def get_state(self) -> AppState:
        async with self._lock:
            # Return a copy so callers cannot mutate the shared snapshot.
            return self._state.model_copy(deep=True)

    async def get_versioned_state(self) -> tuple[int, AppState]:
        async with self._lock:
            return self._version, self._state.model_copy(deep=True)

    async def set_state(self, state: AppState) -> None:
        async with self._condition:
            self._state = state
            self._version += 1
            self._condition.notify_all()

    async def wait_for_update(
        self,
        current_version: int,
        *,
        timeout: float | None = None,
    ) -> tuple[int, AppState]:
        async def _wait() -> tuple[int, AppState]:
            async with self._condition:
                await self._condition.wait_for(lambda: self._version > current_version)
                return self._version, self._state.model_copy(deep=True)

        if timeout is None:
            return await _wait()
        return await asyncio.wait_for(_wait(), timeout=timeout)


state_store = StateStore()
