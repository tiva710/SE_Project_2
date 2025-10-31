# tests/test_graph_routes.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app  # Your FastAPI app
from app.models.schemas import GraphResponse

client = TestClient(app)

# Sample mock data
mock_graph_data = {
    "nodes": [{"id": "n1", "label": "Stakeholder"}],
    "edges": [{"source": "n1", "target": "n2", "type": "CONNECTED_TO"}],
}

# -----------------------------
# Test /stakeholders/overview
# -----------------------------
@patch("app.routes.graph.fetch_same_label_overview")
def test_stakeholders_overview(mock_service):
    mock_service.return_value = mock_graph_data

    response = client.get("/api/graph/stakeholders/overview?limit=100")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["nodes"][0]["id"] == "n1"
    mock_service.assert_called_once_with("Stakeholder", limit=100)


# -----------------------------
# Test /stakeholders/neighborhood
# -----------------------------
@patch("app.routes.graph.fetch_same_label_neighborhood")
def test_stakeholder_neighborhood(mock_service):
    mock_service.return_value = mock_graph_data

    response = client.get("/api/graph/stakeholders/neighborhood?id=test_id&k=2&limit=500")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    mock_service.assert_called_once_with(center_id="test_id", label="Stakeholder", k=2, limit=500)


# -----------------------------
# Test 404 case for /stakeholders/neighborhood
# -----------------------------
@patch("app.routes.graph.fetch_same_label_neighborhood")
def test_stakeholder_neighborhood_not_found(mock_service):
    mock_service.return_value = {"nodes": [], "edges": []}

    response = client.get("/api/graph/stakeholders/neighborhood?id=invalid")
    assert response.status_code == 404
    assert "No nodes found" in response.json()["detail"]


# -----------------------------
# Test /features/neighborhood
# -----------------------------
@patch("app.routes.graph.fetch_same_label_neighborhood")
def test_feature_neighborhood(mock_service):
    mock_service.return_value = mock_graph_data

    response = client.get("/api/graph/features/neighborhood?id=feature1&k=1&limit=500")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    mock_service.assert_called_once_with(center_id="feature1", label="Feature", k=1, limit=500)
