"""Thin client for X's OAuth 2.0 endpoints (Authorization Code + PKCE)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

import requests

from .config import Config
from .errors import TokenError
from .pkce import code_challenge_s256, generate_code_verifier, generate_state
from .token import Token

AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
REVOKE_URL = "https://api.x.com/2/oauth2/revoke"
ME_URL = "https://api.x.com/2/users/me"
TIMEOUT = (5, 20)  # connect, read


@dataclass(frozen=True)
class AuthRequest:
    url: str
    state: str = field(repr=False)
    code_verifier: str = field(repr=False)


class OAuthClient:
    def __init__(self, config: Config, session: requests.Session | None = None) -> None:
        self._config = config
        self._http = session or requests.Session()

    # -- step 1 -----------------------------------------------------------------
    def build_authorization_request(self) -> AuthRequest:
        state = generate_state()
        verifier = generate_code_verifier()
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._config.client_id,
                "redirect_uri": self._config.redirect_uri,
                "scope": self._config.scope_str,
                "state": state,
                "code_challenge": code_challenge_s256(verifier),
                "code_challenge_method": "S256",
            }
        )
        return AuthRequest(url=f"{AUTHORIZE_URL}?{query}", state=state, code_verifier=verifier)

    # -- step 2 -----------------------------------------------------------------
    def exchange_code(self, code: str, code_verifier: str) -> Token:
        return self._token_request(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._config.redirect_uri,
                "code_verifier": code_verifier,
            }
        )

    def refresh(self, refresh_token: str) -> Token:
        return self._token_request({"grant_type": "refresh_token", "refresh_token": refresh_token})

    def revoke(self, token: str, token_type_hint: str = "access_token") -> None:
        data = {"token": token, "token_type_hint": token_type_hint}
        resp = self._post(REVOKE_URL, data)
        if resp.status_code != 200:
            raise TokenError(_describe_error("token revocation failed", resp))

    def get_me(self, access_token: str) -> dict[str, Any]:
        resp = self._http.get(
            ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"user.fields": "id,name,username,verified"},
            timeout=TIMEOUT,
            allow_redirects=False,
        )
        if resp.status_code != 200:
            raise TokenError(_describe_error("users/me request failed", resp))
        return resp.json().get("data", {})

    # -- internals --------------------------------------------------------------
    def _post(self, url: str, data: dict[str, str]) -> requests.Response:
        auth = None
        if self._config.is_confidential:
            auth = (self._config.client_id, self._config.client_secret or "")
        else:
            data = {**data, "client_id": self._config.client_id}
        # allow_redirects=False: never replay credentials to a redirect target.
        return self._http.post(url, data=data, auth=auth, timeout=TIMEOUT, allow_redirects=False)

    def _token_request(self, data: dict[str, str]) -> Token:
        resp = self._post(TOKEN_URL, data)
        if resp.status_code != 200:
            raise TokenError(_describe_error("token request failed", resp))
        try:
            return Token.from_response(resp.json())
        except (ValueError, KeyError) as exc:
            raise TokenError("token endpoint returned a malformed response") from exc


def _describe_error(prefix: str, resp: requests.Response) -> str:
    """Build an error message from only the standard OAuth error fields."""
    detail = ""
    try:
        body = resp.json()
        if isinstance(body, dict):
            parts = [str(body.get(k)) for k in ("error", "error_description", "title", "detail")]
            detail = ": " + " - ".join(p for p in parts if p and p != "None")
    except ValueError:
        pass
    return f"{prefix} (HTTP {resp.status_code}){detail[:300]}"
