import json
import os
import stat

import pytest
from conftest import make_token

from xlogin.errors import StorageError
from xlogin.storage import FileStore


def test_file_store_roundtrip_and_permissions(tmp_path):
    fs = FileStore(tmp_path / "cfg" / "tokens.json")
    fs.save("acct", make_token())
    assert fs.load("acct") == make_token()
    assert stat.S_IMODE(os.stat(fs.path).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(fs.path.parent).st_mode) == 0o700
    assert not [p for p in fs.path.parent.iterdir() if p.name.startswith(".tokens-")]
    fs.delete("acct")
    assert fs.load("acct") is None


def test_file_store_refuses_loose_permissions(tmp_path):
    fs = FileStore(tmp_path / "tokens.json")
    fs.save("a", make_token())
    os.chmod(fs.path, 0o644)
    with pytest.raises(StorageError, match="chmod 600"):
        fs.load("a")


def test_file_store_corrupt(tmp_path):
    fs = FileStore(tmp_path / "tokens.json")
    fs.save("a", make_token())
    fs.path.write_text("{not json")
    with pytest.raises(StorageError):
        fs.load("a")
    fs.path.write_text(json.dumps({"a": {"nope": 1}}))
    with pytest.raises(StorageError):
        fs.load("a")
