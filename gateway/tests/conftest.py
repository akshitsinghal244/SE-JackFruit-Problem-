import importlib.util
import os
import sys

import httpx
import pytest
from fastapi.testclient import TestClient

os.environ.update(RDCP_DEV="1", JWT_SECRET="test-secret-test-secret-test-secret-12", BCRYPT_COST="4",
                  ADMIN_EMAIL="admin@rdcp.test", ADMIN_PASSWORD="AdminPass1", RATE_LIMIT_PER_MIN="1000", SERVICE_API_KEY="k")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import db, ratelimit, services  # noqa: E402
from app.config import settings  # noqa: E402

MOCK = os.path.join(os.path.dirname(__file__), "..", "..", "mock-models", "app.py")


def load_mock(name: str):
    os.environ["MODEL_NAME"] = name
    os.environ["SERVICE_API_KEY"] = "k"
    spec = importlib.util.spec_from_file_location(f"mock_{name}", MOCK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class HostRouter(httpx.AsyncBaseTransport):
    """Route http://ml / http://dl / http://qml to the in-process mock ASGI apps."""
    def __init__(self, apps):
        self.t = {h: httpx.ASGITransport(app=a) for h, a in apps.items()}

    async def handle_async_request(self, request):
        return await self.t[request.url.host].handle_async_request(request)


@pytest.fixture()
def client(tmp_path):
    settings.service_urls = {"ml": "http://ml", "dl": "http://dl", "qml": "http://qml"}
    settings.rate_limit = 1000
    settings.timeout = 2
    db.init_engine(f"sqlite:///{tmp_path}/t.db")
    ratelimit.reset()
    services.reset_breakers()
    apps = {n: load_mock(n).app for n in ("ml", "dl", "qml")}
    services.set_client(httpx.AsyncClient(transport=HostRouter(apps), timeout=2))
    from app.main import create_app
    with TestClient(create_app()) as c:
        c.mocks = apps
        yield c
    services.set_client(None)


def register_login(c, name="ana", email="ana@x.com", pw="Passw0rdA"):
    r = c.post("/api/v1/auth/register", json={"username": name, "email": email, "password": pw})
    assert r.status_code == 201, r.text
    tok = c.post("/api/v1/auth/login", json={"email": email, "password": pw}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture()
def user_h(client):
    return register_login(client)


@pytest.fixture()
def admin_h(client):
    tok = client.post("/api/v1/auth/login", json={"email": "admin@rdcp.test", "password": "AdminPass1"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


GOOD = {"store_id": 3, "item_id": 12, "date": "2017-09-15", "prev_sales": [41, 38, 45, 50, 47, 39, 44]}
