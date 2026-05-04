from __future__ import annotations

from pydantic import BaseModel


class AuthStatusResponse(BaseModel):
    enabled: bool
    authenticated: bool


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
