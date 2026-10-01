import http.client
import threading
import time
from urllib.parse import parse_qs, urlsplit

import pytest
import responses
from conftest import make_token

from xlogin.errors import AuthorizationError, XLoginError
from xlogin.manager import AuthManager
from xlogin.oauth import ME_URL, REVOKE_URL, TOKEN_URL
from xlogin.token import Token

NEW = {
    "token_type": "bearer",
    "expires_in": 7200,
    "access_token": "AT2",
    "refresh_token": "RT2",
    "scope": "s",
}


@responses.activate
def test_full_login_end_to_end_via_loopback(public_cfg, store):
    """Real loopback server + real PKCE; only X's HTTP endpoints are mocked."""
    responses.post(TOKEN_URL, json=NEW)
    mgr = AuthManager(public_cfg, store)
    printed = []
    result = {}

    def run():
        result["tok"] = mgr.login(open_browser=False, out=printed.append, timeout=5)

    t = threading.Thread(target=run)
    t.start()
    time.sleep(0.3)
    url = printed[0].split("  ", 1)[1].strip()
    state = parse_qs(urlsplit(url).query)["state"][0]
    conn = http.client.HTTPConnection("127.0.0.1", 18080, timeout=5)
    conn.request("GET", f"/callback?code=AUTHCODE&state={state}")
    assert conn.getresponse().status == 200
    t.join(5)
    assert result["tok"].access_token == "AT2"
    assert store.load("cid").refresh_token == "RT2"
    body = parse_qs(responses.calls[0].request.body)
    assert body["code"] == ["AUTHCODE"] and len(body["code_verifier"][0]) >= 43


@responses.activate
def test_manual_login_rejects_bad_state_and_stores_nothing(public_cfg, store):
    mgr = AuthManager(public_cfg, store)
    with pytest.raises(AuthorizationError):
        mgr.login(
            manual=True,
            out=lambda s: None,
            read_line=lambda p: f"{public_cfg.redirect_uri}?code=x&state=bad",
        )
    assert store.load("cid") is None and not responses.calls


@responses.activate
def test_manual_login_ok(public_cfg, store):
    responses.post(TOKEN_URL, json=NEW)
    seen = []

    def read_line(_):
        state = parse_qs(urlsplit(seen[0].split("  ", 1)[1].strip()).query)["state"][0]
        return f"{public_cfg.redirect_uri}?code=abc&state={state}"

    AuthManager(public_cfg, store).login(manual=True, out=seen.append, read_line=read_line)
    assert store.load("cid").access_token == "AT2"


@responses.activate
def test_get_token_valid_does_not_hit_network(public_cfg, store):
    store.save("cid", Token("at", time.time() + 3600, "rt"))
    assert AuthManager(public_cfg, store).get_token().access_token == "at"
    assert not responses.calls


@responses.activate
def test_get_token_refreshes_and_persists_rotated_token(public_cfg, store):
    responses.post(TOKEN_URL, json=NEW)
    store.save("cid", Token("old", time.time() - 10, "rt-old"))
    tok = AuthManager(public_cfg, store).get_token()
    assert tok.access_token == "AT2" and store.load("cid").refresh_token == "RT2"
    assert parse_qs(responses.calls[0].request.body)["refresh_token"] == ["rt-old"]


@responses.activate
def test_refresh_keeps_old_refresh_token_if_not_rotated(public_cfg, store):
    responses.post(TOKEN_URL, json={k: v for k, v in NEW.items() if k != "refresh_token"})
    store.save("cid", Token("old", time.time() - 10, "rt-old"))
    assert AuthManager(public_cfg, store).get_token().refresh_token == "rt-old"


def test_get_token_errors(public_cfg, store):
    mgr = AuthManager(public_cfg, store)
    with pytest.raises(XLoginError, match="not logged in"):
        mgr.get_token()
    store.save("cid", Token("old", time.time() - 10, None))
    with pytest.raises(XLoginError, match="no refresh token"):
        mgr.get_token()


@responses.activate
def test_whoami(public_cfg, store):
    responses.get(ME_URL, json={"data": {"id": "1", "username": "u", "name": "N"}})
    store.save("cid", make_token(now=time.time()))
    assert AuthManager(public_cfg, store).whoami()["username"] == "u"
    assert responses.calls[0].request.headers["Authorization"] == "Bearer at"


@responses.activate
def test_logout_revokes_both_tokens_and_deletes(public_cfg, store):
    responses.post(REVOKE_URL, json={"revoked": True})
    store.save("cid", make_token(now=time.time()))
    assert AuthManager(public_cfg, store).logout() is True
    hints = [parse_qs(c.request.body)["token_type_hint"][0] for c in responses.calls]
    assert hints == ["access_token", "refresh_token"] and store.load("cid") is None


@responses.activate
def test_logout_deletes_locally_even_if_revoke_fails(public_cfg, store):
    responses.post(REVOKE_URL, status=500)
    store.save("cid", make_token(now=time.time()))
    assert AuthManager(public_cfg, store).logout() is False
    assert store.load("cid") is None


def test_manual_login_eof_is_a_clean_error(public_cfg, store):
    def eof(_):
        raise EOFError

    with pytest.raises(AuthorizationError, match="stdin closed"):
        AuthManager(public_cfg, store).login(manual=True, out=lambda s: None, read_line=eof)
