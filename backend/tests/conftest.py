"""Points the app at an isolated temp SQLite DB / Chroma path BEFORE any
app.* module is imported anywhere (including by other test files), so tests
never touch the real changepilot.db / chroma_store used for manual runs.
This must stay at module level (not inside a fixture) since app.config
reads these env vars at import time.
"""
import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="changepilot_test_")
os.environ["CHANGEPILOT_DB_PATH"] = os.path.join(_tmp_dir, "test.db")
os.environ["CHANGEPILOT_CHROMA_PATH"] = os.path.join(_tmp_dir, "chroma_store")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-a-real-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    init_db()
    return TestClient(app)
