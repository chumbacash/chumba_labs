from fastapi.testclient import TestClient

from api.server import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_alias_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_smiles_returns_400():
    response = client.post(
        "/api/hplc/run",
        json={
            "modality": "hplc",
            "analytes": [{"name": "broken", "smiles": "not_a_smiles"}],
            "min_resolution": 1.5,
            "max_run_time_min": 12,
        },
    )
    assert response.status_code == 400
    assert "invalid SMILES" in response.json()["error"]


def test_invalid_json_returns_400():
    response = client.post(
        "/api/hplc/run",
        content="{not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json() == {"error": "invalid JSON body"}


def test_gc_ms_returns_stub_payload():
    response = client.post(
        "/api/hplc/run",
        json={
            "modality": "gc_ms",
            "analytes": [{"name": "ethanol", "smiles": "CCO"}],
            "min_resolution": 1.5,
            "max_run_time_min": 12,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["modality"] == "gc_ms"
    assert payload["passed"] is False
    assert payload["iterations"] == 0
