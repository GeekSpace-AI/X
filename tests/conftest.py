import pytest

from xlogin.config import Config
from xlogin.token import Token


class MemoryStore:
    def __init__(self):
        self.data = {}

    def load(self, account):
        return self.data.get(account)

    def save(self, account, token):
        self.data[account] = token

    def delete(self, account):
        self.data.pop(account, None)


@pytest.fixture
def store():
    return MemoryStore()


@pytest.fixture
def public_cfg():
    return Config(client_id="cid", redirect_uri="http://127.0.0.1:18080/callback")


@pytest.fixture
def secret_cfg():
    return Config(
        client_id="cid", client_secret="shh", redirect_uri="http://127.0.0.1:18080/callback"
    )


def make_token(expires_in=7200, refresh="rt", now=1_000_000.0):
    return Token(access_token="at", expires_at=now + expires_in, refresh_token=refresh, scope="a b")
