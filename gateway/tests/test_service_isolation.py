"""TC-14 (SEC-05): microservices are internal-only and require a valid X-API-Key.

Two halves:
  * runtime    - the gateway must send X-API-Key + X-Request-ID on every service call, and must
                 degrade gracefully when a service refuses the key (the services' own 401 behaviour
                 is covered by services/tests/test_api.py).
  * deployment - nothing may publish a host port for ml/dl/qml/db/redis, the internal network must be
                 closed, and the Kubernetes manifests must carry default-deny NetworkPolicies
                 (compose + k8s/base/networkpolicy.yaml).
"""
import pathlib

import yaml

from app import services

from .conftest import GOOD

REPO = pathlib.Path(__file__).resolve().parents[2]


def load(path):
    return list(yaml.safe_load_all((REPO / path).read_text(encoding="utf-8")))


# ------------------------------------------------------------------------- runtime
def test_gateway_sends_api_key_and_request_id_to_every_service(client, user_h):
    import asyncio

    import httpx

    seen = {}

    class Spy(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            seen[request.url.host] = {"key": request.headers.get("X-API-Key"),
                                      "rid": request.headers.get("X-Request-ID")}
            return httpx.Response(401, json={})                    # force the service side to answer

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Spy()))
    try:
        asyncio.run(services.predict(GOOD, "rid-tc14"))
    finally:
        services.set_client(None)

    assert set(seen) == {"ml", "dl", "qml"}
    for host, got in seen.items():
        assert got["key"] == services.settings.service_api_key, host
        assert got["rid"] == "rid-tc14", host                      # correlated in the service logs


def test_orchestrator_treats_401_from_a_service_as_unavailable(client, user_h):
    """A service that refuses the key must degrade, not crash the prediction."""
    import asyncio

    import httpx

    class NoKey(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(401, json={})

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=NoKey()))
    try:
        out = asyncio.run(services.predict(GOOD, "rid-401"))
    finally:
        services.set_client(None)
    assert all(v["status"] == "error" and v["code"] == "SVC_UNAVAILABLE" for v in out.values())


# ---------------------------------------------------------------------- deployment
def test_compose_publishes_ports_only_on_the_edge():
    docs = load("docker-compose.yml")
    compose = docs[0]
    for name, svc in compose["services"].items():
        if name == "edge":
            assert "443:443" in [str(p) for p in svc.get("ports", [])], "the TLS edge must publish 443"
        else:
            assert not svc.get("ports"), f"{name} publishes host ports (SEC-05)"

    assert compose["networks"]["internal"].get("internal") is True, "internal network must be closed"
    both = [n for n, s in compose["services"].items() if set(s.get("networks", [])) == {"public", "internal"}]
    assert both == ["gateway"], f"only the gateway may join both networks, got {both}"
    for internal_only in ("ml", "dl", "qml", "db", "redis"):
        assert compose["services"][internal_only]["networks"] == ["internal"], internal_only


def test_k8s_has_default_deny_and_only_the_gateway_may_reach_the_models():
    policies = [d for doc in load("k8s/base/networkpolicy.yaml") for d in ([doc] if doc else [])]
    assert policies, "no NetworkPolicy found"
    names = {p["metadata"]["name"] for p in policies}
    assert "default-deny-ingress" in names, names
    deny = next(p for p in policies if p["metadata"]["name"] == "default-deny-ingress")
    assert deny["spec"]["podSelector"] == {} and deny["spec"]["policyTypes"] == ["Ingress"]

    models = next(p for p in policies if p["metadata"]["name"] == "allow-gateway-to-models")
    assert models["spec"]["podSelector"]["matchLabels"] == {"tier": "model"}
    assert models["spec"]["ingress"][0]["from"][0]["podSelector"]["matchLabels"] == {"app": "gateway"}

    data = next(p for p in policies if p["metadata"]["name"] == "allow-gateway-to-data")
    assert [p["port"] for p in data["spec"]["ingress"][0]["ports"]] == [5432, 6379]

    kust = load("k8s/base/kustomization.yaml")[0]
    assert "networkpolicy.yaml" in kust["resources"]


def test_models_are_not_exposed_by_a_service_or_ingress():
    for doc in load("k8s/base/models.yaml") + load("k8s/base/ingress.yaml"):
        for item in [doc] if doc else []:
            if item.get("kind") == "Service":
                spec = item.get("spec", {})
                assert spec.get("type") not in ("LoadBalancer", "NodePort"), item["metadata"]["name"]
            if item.get("kind") == "Ingress":
                rules = item["spec"]["rules"][0]["http"]["paths"]
                assert all(p["path"] != "/predict" for p in rules), "model endpoints must not be public"


def test_client_never_talks_to_a_model_service_directly():
    """The React app only ever calls /api/v1, so a browser cannot reach the tier-3 services."""
    src = REPO / "client" / "src"
    assert src.is_dir()
    checked = 0
    for path in sorted(src.rglob("*.js*")):
        if path.name == "styles.css":
            continue
        body = path.read_text(encoding="utf-8", errors="ignore")
        assert "8001" not in body and "8002" not in body and "8003" not in body, path.name
        if "http://" in body or "fetch(" in body:
            assert "/api/v1" in body, path.name
        checked += 1
    assert checked >= 8, checked
