"""Token persistence: OS keyring first, 0600 file as an explicit fallback."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Protocol

from .errors import StorageError
from .token import Token

SERVICE = "xlogin"
_CORRUPT = "stored token is corrupt; run `xlogin logout` and login again"


class TokenStore(Protocol):
    def load(self, account: str) -> Token | None: ...
    def save(self, account: str, token: Token) -> None: ...
    def delete(self, account: str) -> None: ...


class KeyringStore:
    def __init__(self) -> None:
        import keyring
        from keyring.backends import fail

        backend = keyring.get_keyring()
        if isinstance(backend, fail.Keyring) or getattr(backend, "priority", 1) < 1:
            raise StorageError("no usable OS keyring backend available")
        self._kr = keyring

    def load(self, account: str) -> Token | None:
        raw = self._kr.get_password(SERVICE, account)
        if not raw:
            return None
        try:
            return Token.from_dict(json.loads(raw))
        except (ValueError, KeyError) as exc:
            raise StorageError(_CORRUPT) from exc

    def save(self, account: str, token: Token) -> None:
        self._kr.set_password(SERVICE, account, json.dumps(token.to_dict()))

    def delete(self, account: str) -> None:
        with contextlib.suppress(self._kr.errors.PasswordDeleteError):
            self._kr.delete_password(SERVICE, account)


def default_token_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "xlogin" / "tokens.json"


class FileStore:
    """Plain JSON file, directory 0700 / file 0600, written atomically.

    Not encrypted: it relies on filesystem permissions. Use only when no keyring exists.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_token_path()

    def _read_all(self) -> dict[str, dict]:
        try:
            mode = self.path.stat().st_mode & 0o777
            if mode & 0o077:
                raise StorageError(
                    f"{self.path} is accessible by other users (mode {oct(mode)}); "
                    f"run: chmod 600 {self.path}"
                )
            return json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except ValueError as exc:
            raise StorageError(f"{self.path} is corrupt") from exc

    def _write_all(self, data: dict[str, dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".tokens-")  # created 0600
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp)
            raise

    def load(self, account: str) -> Token | None:
        entry = self._read_all().get(account)
        if entry is None:
            return None
        try:
            return Token.from_dict(entry)
        except (KeyError, ValueError) as exc:
            raise StorageError(_CORRUPT) from exc

    def save(self, account: str, token: Token) -> None:
        data = self._read_all()
        data[account] = token.to_dict()
        self._write_all(data)

    def delete(self, account: str) -> None:
        data = self._read_all()
        if data.pop(account, None) is not None:
            self._write_all(data)


def default_store(allow_file_fallback: bool = False) -> TokenStore:
    try:
        return KeyringStore()
    except StorageError:
        if allow_file_fallback:
            return FileStore()
        raise StorageError(
            "no OS keyring available. Install/unlock one, or opt in to the file store "
            "with --insecure-file-store (token saved to a 0600 file)."
        ) from None
