"""Integration tests for database persistence and history endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.session import init_db


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database tables are initialized before each test."""
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


class TestHistoryPersistence:
    """Tests for saving, listing, retrieving, and deleting historical benchmark runs."""

    def test_compare_endpoint_saves_to_history(self, client):
        # 1. Run comparison with save_to_history=True
        compare_payload = {
            "enforce_water_budget": True,
            "save_to_history": True,
            "run_name": "Automated Test Run",
        }
        res_compare = client.post("/api/schedule/compare", json=compare_payload)
        assert res_compare.status_code == 200

        # 2. Check history list
        res_history = client.get("/api/history")
        assert res_history.status_code == 200
        history_list = res_history.json()
        assert len(history_list) >= 1

        latest = history_list[0]
        assert latest["name"] == "Automated Test Run"
        assert latest["enforce_water_budget"] is True
        assert latest["total_jobs"] == 5
        assert latest["carbon_reduction_pct"] is not None
        assert latest["winner_carbon"] is not None

        # 3. Retrieve full detail by ID
        run_id = latest["id"]
        res_detail = client.get(f"/api/history/{run_id}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert detail["id"] == run_id
        assert "comparison_table" in detail["report"]
        assert len(detail["report"]["comparison_table"]) == 6

        # 4. Delete the run
        res_delete = client.delete(f"/api/history/{run_id}")
        assert res_delete.status_code == 200
        assert "successfully deleted" in res_delete.json()["message"]

        # 5. Verify it is gone
        res_gone = client.get(f"/api/history/{run_id}")
        assert res_gone.status_code == 404

    def test_get_nonexistent_history_run_returns_404(self, client):
        res = client.get("/api/history/9999999")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_delete_nonexistent_history_run_returns_404(self, client):
        res = client.delete("/api/history/9999999")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()
