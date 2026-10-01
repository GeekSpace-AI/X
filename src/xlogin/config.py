from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .errors import ConfigError

DEFAULT_REDIRECT_URI = "http://127.0.0.1:8080/callback"
DEFAULT_SCOPES = ("tweet.read", "users.read", "offline.access")
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "[::1]", "::1")


@dataclass(frozen=True)
class Config:
    client_id: str
    client_secret: str | None = field(default=None, repr=False)
    redirect_uri: str = DEFAULT_REDIRECT_URI
    scopes: tuple[str, ...] = DEFAULT_SCOPES

    def __post_init__(self) -> None:
        if not self.client_id or not self.client_id.strip():
            raise ConfigError("X_CLIENT_ID is required")
        if not self.scopes:
            raise ConfigError("at least one scope is required")
        parts = urlsplit(self.redirect_uri)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ConfigError("X_REDIRECT_URI must be an absolute http(s) URL")
        # Plain http is only acceptable on the loopback interface.
        if parts.scheme == "http" and parts.hostname not in LOOPBACK_HOSTS:
            raise ConfigError("X_REDIRECT_URI must use https unless it is a loopback address")
        if parts.fragment:
            raise ConfigError("X_REDIRECT_URI must not contain a fragment")

    @property
    def is_confidential(self) -> bool:
        return bool(self.client_secret)

    @property
    def scope_str(self) -> str:
        return " ".join(self.scopes)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Config:
        env = os.environ if env is None else env
        scopes = env.get("X_SCOPES", "").split() or list(DEFAULT_SCOPES)
        return cls(
            client_id=env.get("X_CLIENT_ID", "").strip(),
            client_secret=(env.get("X_CLIENT_SECRET") or "").strip() or None,
            redirect_uri=(env.get("X_REDIRECT_URI") or DEFAULT_REDIRECT_URI).strip(),
            scopes=tuple(scopes),
        )


def load_dotenv(path: str = ".env") -> None:
    """Tiny .env loader (no dependency). Existing environment variables win."""
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except FileNotFoundError:
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip("'\"")
        os.environ.setdefault(key.strip(), value)
