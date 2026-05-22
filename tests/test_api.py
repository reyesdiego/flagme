from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.testclient import TestClient


def _boolean_flag(
    key: str = "rollout",
    *,
    enabled: bool = True,
    environment: str | None = None,
    user_id: str | None = None,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "description": "",
        "environment": environment,
        "user_id": user_id,
        "starts_at": starts_at.isoformat() if starts_at else None,
        "ends_at": ends_at.isoformat() if ends_at else None,
        "value_type": "boolean",
        "boolean_value": enabled,
        "string_value": None,
    }


def _create(client: TestClient, payload: dict[str, Any]) -> dict[str, Any]:
    r = client.post("/flags", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


def test_list_flags_starts_empty(client: TestClient) -> None:
    assert client.get("/flags").json() == []


def test_create_get_update_delete_round_trip(client: TestClient) -> None:
    created = _create(client, _boolean_flag())
    flag_id = created["id"]

    r = client.get(f"/flags/{flag_id}")
    assert r.status_code == 200
    assert r.json()["key"] == "rollout"

    payload = _boolean_flag(enabled=False)
    r = client.put(f"/flags/{flag_id}", json=payload)
    assert r.status_code == 200
    assert r.json()["boolean_value"] is False

    r = client.delete(f"/flags/{flag_id}")
    assert r.status_code == 204
    assert client.get(f"/flags/{flag_id}").status_code == 404


def test_string_valued_flag(client: TestClient) -> None:
    payload = {
        "key": "checkout-button",
        "description": "label override",
        "environment": None,
        "user_id": None,
        "starts_at": None,
        "ends_at": None,
        "value_type": "string",
        "boolean_value": None,
        "string_value": "Buy now!",
    }
    created = _create(client, payload)
    assert created["string_value"] == "Buy now!"

    r = client.post("/evaluate/checkout-button", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["value_type"] == "string"
    assert body["value"] == "Buy now!"


def test_boolean_flag_requires_boolean_value(client: TestClient) -> None:
    bad = {
        "key": "broken",
        "value_type": "boolean",
        "boolean_value": None,
        "string_value": "oops",
    }
    r = client.post("/flags", json=bad)
    assert r.status_code == 422


def test_time_window_must_be_ordered(client: TestClient) -> None:
    starts = datetime.now(timezone.utc)
    ends = starts - timedelta(hours=1)
    r = client.post(
        "/flags", json=_boolean_flag(starts_at=starts, ends_at=ends)
    )
    assert r.status_code == 422


def test_evaluation_prefers_exact_environment_then_global(client: TestClient) -> None:
    _create(client, _boolean_flag(enabled=False))  # global default off
    _create(client, _boolean_flag(enabled=True, environment="prod"))

    r = client.post("/evaluate/rollout", json={"environment": "prod"})
    assert r.json()["value"] is True

    r = client.post("/evaluate/rollout", json={"environment": "staging"})
    assert r.json()["value"] is False


def test_evaluation_prefers_env_plus_user_over_env_only(client: TestClient) -> None:
    _create(client, _boolean_flag(enabled=False, environment="prod"))
    _create(
        client,
        _boolean_flag(enabled=True, environment="prod", user_id="alice"),
    )

    r = client.post(
        "/evaluate/rollout", json={"environment": "prod", "user_id": "alice"}
    )
    assert r.json()["value"] is True

    r = client.post(
        "/evaluate/rollout", json={"environment": "prod", "user_id": "bob"}
    )
    assert r.json()["value"] is False


def test_evaluation_skips_flag_outside_time_window(client: TestClient) -> None:
    future = datetime.now(timezone.utc) + timedelta(days=1)
    far_future = future + timedelta(days=1)
    _create(
        client,
        _boolean_flag(enabled=True, starts_at=future, ends_at=far_future),
    )
    r = client.post("/evaluate/rollout", json={})
    assert r.status_code == 404


def test_evaluation_unknown_key_returns_404(client: TestClient) -> None:
    assert client.post("/evaluate/missing", json={}).status_code == 404


def test_list_filters_by_environment(client: TestClient) -> None:
    _create(client, _boolean_flag())  # global
    _create(client, _boolean_flag(environment="prod"))
    _create(client, _boolean_flag(environment="staging"))

    r = client.get("/flags?environment=prod")
    envs = [f["environment"] for f in r.json()]
    assert sorted(envs, key=lambda e: e or "") == [None, "prod"]


def test_root_redirects_to_docs(client: TestClient) -> None:
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (307, 308)
    assert r.headers["location"] == "/docs"


def test_openapi_schema_advertises_routes_and_tags(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "flagme"
    assert {tag["name"] for tag in schema["tags"]} == {"System", "Flags", "Evaluation"}
    paths = schema["paths"]
    assert "/healthz" in paths
    assert "/flags" in paths
    assert "/flags/{flag_id}" in paths
    assert "/evaluate/{key}" in paths
    assert "/" not in paths
    schemas = schema["components"]["schemas"]
    assert {"Flag", "FlagInput", "Evaluation", "EvaluationContext"} <= set(schemas)
