"""Integration tests for the AquaGrid FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """TestClient fixture for making API requests."""
    return TestClient(app)


class TestHealthAndInfoEndpoints:
    """Tests for root and health inspection routes."""

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "AquaGrid" in data["message"]
        assert data["docs"] == "/docs"

    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "aquagrid-api"


class TestSitesAndWorkloadsEndpoints:
    """Tests for datacenter sites and workload metadata routes."""

    def test_list_sites(self, client):
        response = client.get("/api/sites")
        assert response.status_code == 200
        sites = response.json()
        assert len(sites) == 3
        site_ids = [s["id"] for s in sites]
        assert "phoenix-01" in site_ids
        assert "quincy-01" in site_ids
        assert "council-bluffs-01" in site_ids

    def test_get_environmental_profile_valid(self, client):
        response = client.get("/api/sites/phoenix-01/environmental")
        assert response.status_code == 200
        data = response.json()
        assert data["site_id"] == "phoenix-01"
        assert len(data["hourly_conditions"]) == 24

    def test_get_environmental_profile_not_found(self, client):
        response = client.get("/api/sites/atlantis-01/environmental")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_canonical_workloads(self, client):
        response = client.get("/api/workloads")
        assert response.status_code == 200
        workloads = response.json()
        assert len(workloads) == 5
        job_ids = [w["id"] for w in workloads]
        assert "job-01" in job_ids


class TestSchedulingEndpoints:
    """Tests for execution, comparison, and diagnostic API endpoints."""

    def test_run_fifo_scheduler(self, client):
        payload = {"scheduler_type": "fifo"}
        response = client.post("/api/schedule/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["scheduler_name"] == "Baseline-1 FIFO"
        assert data["status"] == "FEASIBLE"
        assert data["metrics"]["jobs_scheduled"] == 5

    def test_run_carbon_only_scheduler(self, client):
        payload = {"scheduler_type": "carbon_only"}
        response = client.post("/api/schedule/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["scheduler_name"] == "Baseline-2 Carbon-Only"
        assert data["status"] == "FEASIBLE"

    def test_run_cpsat_preset(self, client):
        payload = {
            "scheduler_type": "cpsat",
            "preset": "water_first",
            "enforce_water_budget": True,
        }
        response = client.post("/api/schedule/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("OPTIMAL", "FEASIBLE")
        assert "WATER_FIRST" in data["notes"]

    def test_run_invalid_scheduler_type(self, client):
        payload = {"scheduler_type": "quantum_annealer"}
        response = client.post("/api/schedule/run", json=payload)
        assert response.status_code == 400
        assert "unknown scheduler_type" in response.json()["detail"].lower()

    def test_compare_schedulers_endpoint(self, client):
        payload = {"enforce_water_budget": True}
        response = client.post("/api/schedule/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["comparison_table"]) == 6
        assert len(data["key_findings"]) >= 2
        assert "winner_for_carbon" in data
        assert "winner_for_water" in data

    def test_diagnose_scenario_endpoint(self, client):
        payload = {}
        response = client.post("/api/schedule/diagnose", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_feasible"] is True
        assert len(data["critical_issues"]) == 0
