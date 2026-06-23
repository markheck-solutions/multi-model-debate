"""Tests for the local GUI runner API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from multi_model_debate.local_app.demo_data import build_default_panel
from multi_model_debate.local_app.schemas import DebateRunRequest, RunLane
from multi_model_debate.local_app.server import create_app


def test_health_endpoint_reports_local_runner() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["lane"] == "local"


def test_catalog_returns_accounts_models_and_default_panel() -> None:
    client = TestClient(create_app())

    response = client.get("/api/models")
    body = response.json()

    assert response.status_code == 200
    assert body["accounts"]
    assert body["models"]
    assert [seat["role"] for seat in body["default_panel"]["seats"]] == [
        "builder",
        "critic_a",
        "critic_b",
        "judge",
    ]
    assert body["default_panel"]["seats"][2]["required"] is False


def test_create_demo_run_and_fetch_final_report() -> None:
    client = TestClient(create_app())
    request = DebateRunRequest(
        question="Should we launch this feature next month?",
        lane=RunLane.DEMO,
        panel=build_default_panel(),
    )

    create_response = client.post("/api/runs", json=request.model_dump(mode="json"))
    run = create_response.json()
    report_response = client.get(f"/api/runs/{run['id']}/artifacts/final")

    assert create_response.status_code == 200
    assert run["status"] == "completed"
    assert "Conditional approval" in report_response.json()


def test_unknown_run_returns_clear_404() -> None:
    client = TestClient(create_app())

    response = client.get("/api/runs/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found."


def test_run_events_websocket_streams_timeline() -> None:
    client = TestClient(create_app())
    request = DebateRunRequest(
        question="Should we launch this feature next month?",
        lane=RunLane.DEMO,
        panel=build_default_panel(),
    )
    run = client.post("/api/runs", json=request.model_dump(mode="json")).json()

    with client.websocket_connect(f"/api/runs/{run['id']}/events") as websocket:
        first_event = websocket.receive_json()

    assert first_event["phase"] == "build"
    assert first_event["status"] == "running"
