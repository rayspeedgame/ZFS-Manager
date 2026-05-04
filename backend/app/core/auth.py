from __future__ import annotations

import hashlib

from fastapi import HTTPException, Request, Response, WebSocket, status

from app import runtime


AUTH_COOKIE_NAME = "zfs_manager_auth"


def auth_is_enabled() -> bool:
    return bool(runtime.config.auth.enabled and (runtime.config.auth.password or "").strip())


def auth_cookie_value(password: str | None = None) -> str:
    secret = str(password if password is not None else runtime.config.auth.password or "")
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def request_is_authenticated(request: Request) -> bool:
    if not auth_is_enabled():
        return True
    return request.cookies.get(AUTH_COOKIE_NAME) == auth_cookie_value()


def websocket_is_authenticated(websocket: WebSocket) -> bool:
    if not auth_is_enabled():
        return True
    return websocket.cookies.get(AUTH_COOKIE_NAME) == auth_cookie_value()


def require_authenticated_request(request: Request) -> None:
    if request_is_authenticated(request):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
    )


def set_auth_cookie(response: Response) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=auth_cookie_value(),
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
    )
