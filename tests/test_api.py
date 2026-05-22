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
