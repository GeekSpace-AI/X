"""One-shot loopback HTTP server that receives the OAuth redirect.

Hardening:
  * binds to the loopback interface only
  * validates the Host header (blocks DNS-rebinding)
  * accepts exactly one request on the registered path, then shuts down
  * never reflects request data into the response
  * verifies `state` in constant time
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from .errors import AuthorizationError
from .pkce import states_match

_PAGE = (
    "<!doctype html><meta charset=utf-8><title>xlogin</title>"
    "<body style='font-family:sans-serif;text-align:center;margin-top:20vh'>"
    "<h2>{msg}</h2><p>You can close this tab and return to the terminal.</p>"
)


@dataclass
class CallbackResult:
    code: str | None = field(default=None, repr=False)
    state: str | None = field(default=None, repr=False)
    error: str | None = None


def extract_code(redirect_url: str, expected_state: str) -> str:
    """Validate a redirect URL (from the server or pasted by the user) and return the code."""
    query = parse_qs(urlsplit(redirect_url).query)
    return _validate(
        CallbackResult(
            code=_first(query, "code"),
            state=_first(query, "state"),
            error=_first(query, "error"),
        ),
        expected_state,
    )


def _first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def _validate(result: CallbackResult, expected_state: str) -> str:
    if result.error:
        # `error` is an RFC 6749 token (e.g. access_denied); keep only a safe subset.
        safe = "".join(c for c in result.error if c.isalnum() or c in "_-")[:64]
        raise AuthorizationError(f"authorization failed: {safe}")
    if not states_match(expected_state, result.state):
        raise AuthorizationError("state mismatch - possible CSRF, aborting")
    if not result.code:
        raise AuthorizationError("authorization response did not contain a code")
    return result.code


class _Server(HTTPServer):
    # POSIX: lets us rebind through TIME_WAIT yet still refuses an active listener.
    # Windows: SO_REUSEADDR would let another process share/hijack the port, so keep it off.
    allow_reuse_address = os.name != "nt"
    result: CallbackResult | None = None
    done: threading.Event
    path: str
    allowed_hosts: frozenset[str]


class _Handler(BaseHTTPRequestHandler):
    server: _Server

    def log_message(self, *args: object) -> None:  # silence: URLs contain the auth code
        return

    def do_GET(self) -> None:
        parts = urlsplit(self.path)
        host = (self.headers.get("Host") or "").lower()
        if host not in self.server.allowed_hosts:
            return self._reply(400, "Bad request")
        if parts.path != self.server.path or self.server.result is not None:
            return self._reply(404, "Not found")
        query = parse_qs(parts.query)
        self.server.result = CallbackResult(
            code=_first(query, "code"), state=_first(query, "state"), error=_first(query, "error")
        )
        ok = self.server.result.error is None
        self._reply(200 if ok else 400, "Login received" if ok else "Login failed")
        self.server.done.set()

    def _reply(self, status: int, msg: str) -> None:
        body = _PAGE.format(msg=msg).encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


class LoopbackServer:
    def __init__(self, redirect_uri: str) -> None:
        parts = urlsplit(redirect_uri)
        host = parts.hostname or "127.0.0.1"
        port = parts.port or 80
        bind = "::1" if host in ("::1", "[::1]") else "127.0.0.1"
        try:
            self._server = _Server((bind, port), _Handler)
        except OSError as exc:
            raise AuthorizationError(
                f"cannot listen on {bind}:{port} ({exc.strerror}); free the port or use --manual"
            ) from exc
        self._server.path = parts.path or "/"
        self._server.done = threading.Event()
        self._server.allowed_hosts = frozenset({f"{host}:{port}", f"[{host}]:{port}"})
        self._serving = False

    @property
    def port(self) -> int:
        return self._server.server_address[1]

    def wait_for_code(self, expected_state: str, timeout: float = 180.0) -> str:
        thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._serving = True
        thread.start()
        try:
            if not self._server.done.wait(timeout):
                raise AuthorizationError(f"timed out after {int(timeout)}s waiting for login")
            assert self._server.result is not None  # noqa: S101
            return _validate(self._server.result, expected_state)
        finally:
            self.close()
            thread.join(timeout=5)

    def close(self) -> None:
        """Idempotent; safe whether or not wait_for_code() ran."""
        if self._serving:
            self._serving = False
            self._server.shutdown()
        self._server.server_close()
