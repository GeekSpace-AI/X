import base64
from urllib.parse import parse_qs, urlsplit

import pytest
import responses

from xlogin.errors import TokenError
from xlogin.oauth import REVOKE_URL, TOKEN_URL, OAuthClient
from xlogin.pkce import code_challenge_s256

OK = {
    "token_type": "bearer",
    "expires_in": 7200,
    "access_token": "AT",
    "refresh_token": "RT",
    "scope": "tweet.read",
}


def test_authorization_url(public_cfg):
    req = OAuthClient(public_cfg).build_authorization_request()
    u = urlsplit(req.url)
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    assert f"{u.scheme}://{u.netloc}{u.path}" == "https://x.com/i/oauth2/authorize"
    assert q["response_type"] == "code" and q["client_id"] == "cid"
    assert q["code_challenge_method"] == "S256"
    assert q["code_challenge"] == code_challenge_s256(req.code_verifier)
    assert q["state"] == req.state and q["redirect_uri"] == public_cfg.redirect_uri
    assert "code_verifier" not in req.url and req.code_verifier not in repr(req)


@responses.activate
def test_exchange_public_client_sends_client_id_in_body(public_cfg):
    responses.post(TOKEN_URL, json=OK)
    tok = OAuthClient(public_cfg).exchange_code("CODE", "VER")
    call = responses.calls[0].request
    body = parse_qs(call.body)
    assert body["client_id"] == ["cid"] and body["code_verifier"] == ["VER"]
    assert body["grant_type"] == ["authorization_code"] and body["code"] == ["CODE"]
    assert "Authorization" not in call.headers
    assert tok.access_token == "AT" and tok.refresh_token == "RT"


@responses.activate
def test_exchange_confidential_client_uses_basic_auth(secret_cfg):
    responses.post(TOKEN_URL, json=OK)
    OAuthClient(secret_cfg).exchange_code("CODE", "VER")
    call = responses.calls[0].request
    assert call.headers["Authorization"] == "Basic " + base64.b64encode(b"cid:shh").decode()
    assert "client_id" not in parse_qs(call.body)


@responses.activate
def test_refresh_and_revoke(public_cfg):
    responses.post(TOKEN_URL, json=OK)
    responses.post(REVOKE_URL, json={"revoked": True})
    c = OAuthClient(public_cfg)
    c.refresh("RT0")
    assert parse_qs(responses.calls[0].request.body)["grant_type"] == ["refresh_token"]
    c.revoke("AT")
    assert parse_qs(responses.calls[1].request.body)["token"] == ["AT"]


@responses.activate
def test_error_message_has_no_secrets_and_is_bounded(public_cfg):
    responses.post(
        TOKEN_URL,
        status=400,
        json={"error": "invalid_grant", "error_description": "bad", "access_token": "LEAK"},
    )
    with pytest.raises(TokenError) as ei:
        OAuthClient(public_cfg).exchange_code("c", "v")
    assert "invalid_grant" in str(ei.value) and "LEAK" not in str(ei.value)


@responses.activate
def test_redirect_not_followed(public_cfg):
    responses.post(TOKEN_URL, status=302, headers={"Location": "https://evil.example/steal"})
    with pytest.raises(TokenError):
        OAuthClient(public_cfg).exchange_code("c", "v")
    assert len(responses.calls) == 1


@responses.activate
def test_malformed_token_response(public_cfg):
    responses.post(TOKEN_URL, json={"unexpected": 1})
    with pytest.raises(TokenError):
        OAuthClient(public_cfg).exchange_code("c", "v")
