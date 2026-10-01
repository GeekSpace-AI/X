from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

EXPIRY_SKEW_SECONDS = 60


@dataclass(frozen=True)
class Token:
    access_token: str = field(repr=False)
    expires_at: float
    refresh_token: str | None = field(default=None, repr=False)
    scope: str = ""
    token_type: str = "bearer"

    def is_expired(self, skew: int = EXPIRY_SKEW_SECONDS, now: float | None = None) -> bool:
        return (time.time() if now is None else now) >= self.expires_at - skew

    @classmethod
    def from_response(cls, data: dict[str, Any], now: float | None = None) -> Token:
        now = time.time() if now is None else now
        return cls(
            access_token=data["access_token"],
            expires_at=now + int(data.get("expires_in", 7200)),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope", ""),
            token_type=str(data.get("token_type", "bearer")).lower(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "scope": self.scope,
            "token_type": self.token_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Token:
        return cls(
            access_token=data["access_token"],
            expires_at=float(data["expires_at"]),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope", ""),
            token_type=data.get("token_type", "bearer"),
        )
