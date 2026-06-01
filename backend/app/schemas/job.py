from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    description: str = Field(min_length=50)
    session_id: str | None = Field(default=None, max_length=120)


class JobFromUrlCreate(BaseModel):
    url: str = Field(min_length=10, max_length=2048)
    title: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    session_id: str | None = Field(default=None, max_length=120)
    parse_immediately: bool = False


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    company: str | None
    location: str | None = None
    description: str
    status: str
    source_url: str | None = None
    work_mode: str = "unknown"
    employment_type: str = "unknown"
    seniority: str = "unknown"
    parse_status: str
    parse_confidence: float | None
    parsed_json: dict[str, Any] | None
    session_id: str | None
    created_at: datetime
    updated_at: datetime
