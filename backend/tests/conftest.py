import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Configure the app for tests *before* importing it.
os.environ.update(
    DATABASE_URL="sqlite:///./test.db",
    RUN_JOBS_INLINE="true",
    ALLOW_PRIVATE_URLS="true",
    ANTHROPIC_API_KEY="",
    SECRET_KEY="test-secret-key-that-is-long-enough-for-hs256",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

SITES_DIR = Path(__file__).parent / "sites"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep test output clean
        pass


@pytest.fixture(scope="session")
def site_url():
    """Serve tests/sites/ on a random local port."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_QuietHandler, directory=str(SITES_DIR)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    res = client.post("/api/auth/register",
                      json={"email": "sadia@txlabz.com", "name": "Sadia", "password": "password123"})
    client.headers["Authorization"] = f"Bearer {res.json()['access_token']}"
    return client
