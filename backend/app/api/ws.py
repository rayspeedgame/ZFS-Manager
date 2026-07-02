from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.auth import websocket_is_authenticated
from app.core.client_tracker import client_tracker
from app.core.state import state_store


router = APIRouter(tags=["ws"])


@router.websocket("/ws/state")
async def state_stream(websocket: WebSocket) -> None:
    """Push the newest state snapshot to connected clients."""
    if not websocket_is_authenticated(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await websocket.accept()
    await client_tracker.add()
    version, state = await state_store.get_versioned_state()
    await websocket.send_json(state.model_dump(mode="json"))

    try:
        while True:
            try:
                # Send a fresh snapshot whenever the poller updates the state store.
                version, state = await state_store.wait_for_update(version, timeout=30.0)
                await websocket.send_json(state.model_dump(mode="json"))
            except TimeoutError:
                # Keep the connection alive even when the state is temporarily unchanged.
                await websocket.send_json((await state_store.get_state()).model_dump(mode="json"))
    except TimeoutError:
        return
    except (WebSocketDisconnect, asyncio.CancelledError):
        return
    finally:
        await client_tracker.remove()
