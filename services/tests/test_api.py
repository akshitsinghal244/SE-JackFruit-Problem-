"""HTTP contract tests for the shared FastAPI layer (uses the ML model; skipped without fastapi)."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from tests.conftest import train  # noqa: E402

KEY = "test-key"
BODY = {"store_id": 1, "item_id": 2, "date": "2017-09-15", "prev_sales": [41, 38, 45, 50, 47, 39, 44]}


@pytest.fixture(scope="module")
def client(synthetic_csv, tmp_path_factory):
    out = str(tmp_path_factory.mktemp("ml"))
    train("ml_service.train", synthetic_csv, out, "--algo", "rf")
    mp = pytest.MonkeyPatch()
    mp.setenv("MODEL_DIR", out)
    mp.setenv("SERVICE_API_KEY", KEY)
    from ml_service.predictor import MLPredictor
    from shared.service import create_app
    with TestClient(create_app("ml", MLPredictor)) as c:
        yield c
    mp.undo()


H = {"X-API-Key": KEY}


def test_predict_ok(client):
    r = client.post("/predict", json=BODY, headers=H)
    assert r.status_code == 200
    j = r.json()
    assert j["model"] == "ml" and j["category"] in {"Low", "Medium", "High"}
    assert set(j) == {"model", "category", "confidence", "probabilities", "accuracy", "latency_ms"}
    assert "X-Request-ID" in r.headers


def test_missing_or_wrong_key_is_401(client):
    assert client.post("/predict", json=BODY).status_code == 401
    r = client.post("/predict", json=BODY, headers={"X-API-Key": "nope"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "AUTH_INVALID"


@pytest.mark.parametrize("patch", [
    {"prev_sales": [1, 2, 3]},                      # wrong length
    {"prev_sales": [1, 2, 3, 4, 5, 6, -1]},         # negative
    {"date": "15-09-2017"},                         # bad date format
    {"store_id": 999},                              # unknown store
    {"store_id": "1; DROP TABLE users"},            # wrong type
    {"extra_field": 1},                             # not whitelisted
])
def test_validation_errors_are_422_with_details(client, patch):
    r = client.post("/predict", json={**BODY, **patch}, headers=H)
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR" and err["details"] and err["request_id"]


def test_health_and_model_info(client):
    assert client.get("/health", headers=H).json() == {"status": "UP", "model_loaded": True}
    info = client.get("/model-info", headers=H).json()
    assert set(info) == {"algorithm", "version", "accuracy", "macro_f1", "trained_on"}


def test_service_reports_down_when_model_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_DIR", str(tmp_path))  # empty folder
    monkeypatch.setenv("SERVICE_API_KEY", KEY)
    from ml_service.predictor import MLPredictor
    from shared.service import create_app
    with TestClient(create_app("ml", MLPredictor)) as c:
        r = c.get("/health", headers=H)
        assert r.status_code == 503 and r.json()["model_loaded"] is False
        r = c.post("/predict", json=BODY, headers=H)
        assert r.status_code == 503 and r.json()["error"]["code"] == "SVC_UNAVAILABLE"
