"""PKCE (RFC 7636) and state helpers. All randomness comes from `secrets`."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


def generate_code_verifier() -> str:
    # 64 random bytes -> 86 url-safe chars, within the RFC 7636 range of 43..128.
    return secrets.token_urlsafe(64)


def code_challenge_s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def states_match(expected: str, received: str | None) -> bool:
    if not received:
        return False
    return hmac.compare_digest(expected.encode(), received.encode())
