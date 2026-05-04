from __future__ import annotations

from pydantic import BaseModel

from app.core.config import SSHSettings


class SSHConnectionTestRequest(BaseModel):
    ssh: SSHSettings


class SSHConnectionTestResponse(BaseModel):
    success: bool
    message: str
