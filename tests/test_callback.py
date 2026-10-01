import http.client
import threading
import time

import pytest

from xlogin.callback import LoopbackServer, extract_code
from xlogin.errors import AuthorizationError

PORT = 18123
URI = f"http://127.0.0.1:{PORT}/callback"


def _get(path, host=None):
    conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=5)
    conn.putrequest("GET", path, skip_host=True)
    conn.putheader("Host", host or f"127.0.0.1:{PORT}")
    conn.endheaders()
    resp = conn.getresponse()
    return resp.status, resp.read().decode(), dict(resp.getheaders())


def _serve(state="S", timeout=5):
    srv = LoopbackServer(URI)
    out = {}

    def run():
        try:
            out["code"] = srv.wait_for_code(state, timeout=timeout)
        except Exception as exc:
            out["err"] = exc

    t = threading.Thread(target=run)
    t.start()
    time.sleep(0.2)
    return t, out


def test_happy_path_and_hardened_headers():
    t, out = _serve()
    status, body, headers = _get("/callback?code=THECODE&state=S")
    t.join(5)
    assert status == 200 and out == {"code": "THECODE"}
    assert "THECODE" not in body  # nothing reflected
    assert headers["Cache-Control"] == "no-store" and headers["Referrer-Policy"] == "no-referrer"


def test_state_mismatch_rejected():
    t, out = _serve()
    _get("/callback?code=C&state=WRONG")
    t.join(5)
    assert isinstance(out["err"], AuthorizationError) and "state" in str(out["err"])


def test_provider_error_rejected_and_sanitized():
    t, out = _serve()
    status, body, _ = _get("/callback?error=access_denied&state=S")
    t.join(5)
    assert status == 400 and "access_denied" in str(out["err"])


def test_wrong_path_and_rebinding_host_ignored_then_real_request_works():
    t, out = _serve()
    assert _get("/other?code=X&state=S")[0] == 404
    assert _get("/callback?code=X&state=S", host="evil.example.com")[0] == 400
    assert not out  # still waiting
    _get("/callback?code=GOOD&state=S")
    t.join(5)
    assert out == {"code": "GOOD"}


def test_timeout():
    t, out = _serve(timeout=0.5)
    t.join(5)
    assert "timed out" in str(out["err"])


def test_port_released_after_use():
    t, _ = _serve(timeout=0.3)
    t.join(5)
    LoopbackServer(URI).close()  # rebinding works => socket closed


def test_extract_code_for_manual_flow():
    assert extract_code(f"{URI}?code=ZZ&state=S", "S") == "ZZ"
    for bad in (
        f"{URI}?code=ZZ",
        f"{URI}?state=S",
        f"{URI}?error=access_denied&state=S",
        f"{URI}?code=Z&state=T",
    ):
        with pytest.raises(AuthorizationError):
            extract_code(bad, "S")
