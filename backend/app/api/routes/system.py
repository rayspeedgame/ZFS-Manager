from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from app import runtime
from app.core.auth import (
    auth_is_enabled,
    clear_auth_cookie,
    require_authenticated_request,
    request_is_authenticated,
    set_auth_cookie,
)
from app.core.config import AppConfig, save_config
from app.core.state import state_store
from app.schemas.auth import AuthStatusResponse, LoginRequest, LoginResponse
from app.schemas.settings import SettingsSaveResponse
from app.schemas.ssh_test import SSHConnectionTestRequest, SSHConnectionTestResponse
from app.schemas.zfs_state import AppState
from app.ssh.client import SSHClient, SSHConfig

router = APIRouter(prefix="/api")


@router.get("/state", response_model=AppState, tags=["state"])
async def get_state(request: Request) -> AppState:
    """Return the latest in-memory snapshot used by the frontend."""
    require_authenticated_request(request)
    return await state_store.get_state()


@router.post("/state/refresh", response_model=AppState, tags=["system"])
async def force_refresh_state(request: Request) -> AppState:
    """Force a full backend refresh instead of only returning cached state."""
    require_authenticated_request(request)
    return await runtime.poller.refresh_once(force_all=True)


@router.get("/auth/status", response_model=AuthStatusResponse, tags=["auth"])
async def get_auth_status(request: Request) -> AuthStatusResponse:
    return AuthStatusResponse(
        enabled=auth_is_enabled(),
        authenticated=request_is_authenticated(request),
    )


@router.post("/auth/login", response_model=LoginResponse, tags=["auth"])
async def login(payload: LoginRequest, response: Response) -> LoginResponse:
    if not auth_is_enabled():
        return LoginResponse(success=True, message="Authentication is disabled.")

    if payload.password != (runtime.config.auth.password or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )

    set_auth_cookie(response)
    return LoginResponse(success=True, message="Login succeeded.")


@router.post("/auth/logout", response_model=LoginResponse, tags=["auth"])
async def logout(response: Response) -> LoginResponse:
    clear_auth_cookie(response)
    return LoginResponse(success=True, message="Logged out.")


@router.get("/settings", response_model=AppConfig, tags=["system"])
async def get_settings(request: Request) -> AppConfig:
    """Return the currently active backend configuration."""
    require_authenticated_request(request)
    return runtime.config.model_copy(deep=True)


@router.put("/settings", response_model=SettingsSaveResponse, tags=["system"])
async def save_settings(payload: AppConfig, request: Request, response: Response) -> SettingsSaveResponse:
    """Persist backend settings and reload long-lived runtime services."""
    require_authenticated_request(request)
    if payload.auth.enabled and not (payload.auth.password or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login password is required when password login is enabled.",
        )
    config_path = save_config(payload)
    next_config = await runtime.reload_runtime(payload)
    if next_config.auth.enabled and (next_config.auth.password or "").strip():
        set_auth_cookie(response)
    else:
        clear_auth_cookie(response)
    return SettingsSaveResponse(
        config=next_config,
        config_path=str(config_path),
        reloaded=True,
        message="Settings saved and runtime reloaded.",
    )


@router.post("/settings/test-ssh", response_model=SSHConnectionTestResponse, tags=["system"])
async def test_ssh_connection(payload: SSHConnectionTestRequest, request: Request) -> SSHConnectionTestResponse:
    """Test SSH connectivity with the provided settings without saving them."""
    require_authenticated_request(request)
    client = SSHClient(
        SSHConfig(
            host=payload.ssh.host,
            username=payload.ssh.username,
            port=payload.ssh.port,
            password=payload.ssh.password,
            known_hosts=payload.ssh.known_hosts,
            client_keys=payload.ssh.key_files,
            connect_timeout=payload.ssh.connect_timeout,
            keepalive_interval=payload.ssh.keepalive_interval,
            keepalive_count_max=payload.ssh.keepalive_count_max,
        )
    )

    try:
        await client.connect()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"SSH connection test failed: {exc}") from exc
    finally:
        await client.close()

    return SSHConnectionTestResponse(
        success=True,
        message="SSH connection succeeded.",
    )


@router.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
