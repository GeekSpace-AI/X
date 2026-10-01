from __future__ import annotations

import sys
import webbrowser
from collections.abc import Callable
from typing import Any

from .callback import LoopbackServer, extract_code
from .config import Config
from .errors import AuthorizationError, XLoginError
from .oauth import OAuthClient
from .storage import TokenStore
from .token import Token


class AuthManager:
    """Orchestrates login / refresh / logout. One account per client_id."""

    def __init__(self, config: Config, store: TokenStore, oauth: OAuthClient | None = None) -> None:
        self._config = config
        self._store = store
        self._oauth = oauth or OAuthClient(config)

    @property
    def account(self) -> str:
        return self._config.client_id

    def login(
        self,
        open_browser: bool = True,
        manual: bool = False,
        timeout: float = 180.0,
        out: Callable[[str], None] = print,
        read_line: Callable[[str], str] = input,
    ) -> Token:
        req = self._oauth.build_authorization_request()
        # Bind the port before opening the browser so a conflict fails fast.
        server = None if manual else LoopbackServer(self._config.redirect_uri)
        try:
            out("Open this URL in your browser to authorize:\n\n  " + req.url + "\n")
            if open_browser and not manual:
                webbrowser.open(req.url)
            if server is not None:
                code = server.wait_for_code(req.state, timeout=timeout)
            else:
                try:
                    pasted = read_line("Paste the full redirect URL here: ").strip()
                except EOFError:
                    raise AuthorizationError("no redirect URL provided (stdin closed)") from None
                if not pasted:
                    raise AuthorizationError("no redirect URL provided")
                code = extract_code(pasted, req.state)
        finally:
            if server is not None:
                server.close()
        token = self._oauth.exchange_code(code, req.code_verifier)
        self._store.save(self.account, token)
        return token

    def stored_token(self) -> Token | None:
        return self._store.load(self.account)

    def get_token(self) -> Token:
        """Return a valid token, refreshing (and persisting the rotated one) if needed."""
        token = self._store.load(self.account)
        if token is None:
            raise XLoginError("not logged in; run `xlogin login`")
        if not token.is_expired():
            return token
        if not token.refresh_token:
            raise XLoginError("access token expired and no refresh token; run `xlogin login`")
        return self._persist_refreshed(token)

    def _persist_refreshed(self, token: Token) -> Token:
        assert token.refresh_token  # noqa: S101
        new = self._oauth.refresh(token.refresh_token)
        # X rotates refresh tokens: keep the old one only if none was returned.
        if new.refresh_token is None:
            new = Token(
                new.access_token, new.expires_at, token.refresh_token, new.scope or token.scope
            )
        self._store.save(self.account, new)
        return new

    def force_refresh(self) -> Token:
        token = self._store.load(self.account)
        if token is None or not token.refresh_token:
            raise XLoginError("no refresh token; run `xlogin login`")
        return self._persist_refreshed(token)

    def whoami(self) -> dict[str, Any]:
        return self._oauth.get_me(self.get_token().access_token)

    def logout(self) -> bool:
        """Revoke remotely (best effort), always delete locally. True if revoke succeeded."""
        token = self._store.load(self.account)
        if token is None:
            return True
        revoked = True
        try:
            self._oauth.revoke(token.access_token)
            if token.refresh_token:
                self._oauth.revoke(token.refresh_token, "refresh_token")
        except XLoginError as exc:
            revoked = False
            print(f"warning: remote revoke failed: {exc}", file=sys.stderr)
        finally:
            self._store.delete(self.account)
        return revoked
