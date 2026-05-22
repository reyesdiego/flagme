from fastapi.testclient import TestClient

from flagme.api import app

client = TestClient(app)


def test_healthz() -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_flags_starts_empty() -> None:
    r = client.get("/flags")
    assert r.status_code == 200
    assert r.json() == []


def test_upsert_then_get_then_delete() -> None:
    flag = {"key": "checkout-v2", "enabled": True, "description": "rollout"}

    r = client.put("/flags/checkout-v2", json=flag)
    assert r.status_code == 200
    assert r.json() == flag

    r = client.get("/flags/checkout-v2")
    assert r.json() == flag

    r = client.delete("/flags/checkout-v2")
    assert r.status_code == 204

    r = client.get("/flags/checkout-v2")
    assert r.status_code == 404


def test_upsert_rejects_mismatched_key() -> None:
    r = client.put(
        "/flags/foo", json={"key": "bar", "enabled": False, "description": ""}
    )
    assert r.status_code == 400


def test_get_unknown_flag_returns_404() -> None:
    r = client.get("/flags/does-not-exist")
    assert r.status_code == 404


def _put(key: str, *, enabled: bool) -> None:
    r = client.put(
        f"/flags/{key}",
        json={"key": key, "enabled": enabled, "description": ""},
    )
    assert r.status_code == 200


def test_evaluate_enabled_flag() -> None:
    _put("rollout", enabled=True)
    r = client.post("/evaluate/rollout", json={})
    assert r.status_code == 200
    assert r.json() == {"key": "rollout", "value": True, "reason": "FLAG_ENABLED"}


def test_evaluate_disabled_flag() -> None:
    _put("rollout", enabled=False)
    r = client.post("/evaluate/rollout", json={})
    assert r.status_code == 200
    assert r.json() == {"key": "rollout", "value": False, "reason": "FLAG_DISABLED"}


def test_evaluate_accepts_context_with_arbitrary_fields() -> None:
    _put("rollout", enabled=True)
    r = client.post(
        "/evaluate/rollout",
        json={"subject": "user-42", "region": "us-east-1", "plan": "pro"},
    )
    assert r.status_code == 200
    assert r.json()["value"] is True


def test_evaluate_without_body() -> None:
    _put("rollout", enabled=True)
    r = client.post("/evaluate/rollout")
    assert r.status_code == 200
    assert r.json()["value"] is True


def test_evaluate_unknown_flag_returns_404() -> None:
    r = client.post("/evaluate/missing", json={})
    assert r.status_code == 404


def test_root_redirects_to_docs() -> None:
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (307, 308)
    assert r.headers["location"] == "/docs"


def test_docs_endpoint_loads() -> None:
    r = client.get("/docs")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_openapi_schema_advertises_routes_and_tags() -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()

    assert schema["info"]["title"] == "flagme"
    assert {tag["name"] for tag in schema["tags"]} == {"System", "Flags", "Evaluation"}

    paths = schema["paths"]
    assert "/healthz" in paths
    assert "/flags" in paths
    assert "/flags/{key}" in paths
    assert "/evaluate/{key}" in paths
    # The root redirect is intentionally hidden from the schema
    assert "/" not in paths

    assert schema["paths"]["/evaluate/{key}"]["post"]["tags"] == ["Evaluation"]
    assert {"Flag", "Evaluation", "EvaluationContext"} <= set(
        schema["components"]["schemas"]
    )
