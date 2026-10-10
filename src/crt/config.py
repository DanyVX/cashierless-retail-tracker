"""Fail-closed application configuration; no personal data in settings."""

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application configuration for CPU-first research runs."""

    model_config = SettingsConfigDict(env_prefix="CRT_", env_file=".env", extra="ignore")

    blur_faces: bool = True
    require_consent: bool = True
    store_raw_frames: bool = False
    retention_seconds: int = Field(default=0, ge=0)
    log_format: Literal["text", "json"] = "json"

    @model_validator(mode="after")
    def ensure_safe_storage(self) -> "Settings":
        if self.store_raw_frames:
            raise ValueError("Raw frame storage is unavailable until encrypted TTL storage exists")
        if self.retention_seconds != 0:
            raise ValueError("Nonzero retention is unsupported before privacy milestone M7")
        if not self.require_consent:
            raise ValueError("Participant consent cannot be disabled")
        return self
