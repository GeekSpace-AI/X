import base64
import hashlib

import pytest

from xlogin.config import Config, ConfigError
from xlogin.pkce import code_challenge_s256, generate_code_verifier, generate_state, states_match
from xlogin.token import Token


def test_pkce_rfc7636_vector():
    # Appendix B of RFC 7636
    v = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    assert code_challenge_s256(v) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


def test_verifier_length_and_uniqueness():
    a, b = generate_code_verifier(), generate_code_verifier()
    assert 43 <= len(a) <= 128 and a != b
    expected = base64.urlsafe_b64encode(hashlib.sha256(a.encode()).digest()).rstrip(b"=").decode()
    assert code_challenge_s256(a) == expected


def test_state():
    s = generate_state()
    assert states_match(s, s)
    assert not states_match(s, "other") and not states_match(s, None) and not states_match(s, "")


def test_config_from_env_defaults_and_secret_hidden():
    cfg = Config.from_env({"X_CLIENT_ID": " abc ", "X_CLIENT_SECRET": "topsecret"})
    assert cfg.client_id == "abc" and cfg.is_confidential
    assert "offline.access" in cfg.scopes
    assert "topsecret" not in repr(cfg)


@pytest.mark.parametrize(
    "env",
    [
        {},  # no client id
        {"X_CLIENT_ID": "a", "X_REDIRECT_URI": "http://evil.example.com/cb"},  # http, non-loopback
        {"X_CLIENT_ID": "a", "X_REDIRECT_URI": "ftp://127.0.0.1/cb"},
        {"X_CLIENT_ID": "a", "X_REDIRECT_URI": "not a url"},
        {"X_CLIENT_ID": "a", "X_REDIRECT_URI": "https://x.example.com/cb#frag"},
    ],
)
def test_config_rejects_bad_input(env):
    with pytest.raises(ConfigError):
        Config.from_env(env)


def test_config_allows_https_remote():
    Config(client_id="a", redirect_uri="https://app.example.com/cb")


def test_token_expiry_and_repr_redacts():
    t = Token.from_response(
        {"access_token": "SECRET1", "refresh_token": "SECRET2", "expires_in": 100}, now=0
    )
    assert t.is_expired(skew=0, now=100) and not t.is_expired(skew=0, now=99)
    assert t.is_expired(skew=60, now=50)
    assert "SECRET1" not in repr(t) and "SECRET2" not in repr(t)
    assert Token.from_dict(t.to_dict()) == t
