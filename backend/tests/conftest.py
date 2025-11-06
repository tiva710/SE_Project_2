import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app


@pytest.fixture
def test_client():
    """Fixture for FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_neo4j_driver():
    """Fixture for mocked Neo4j driver"""
    with patch('app.services.neo4j_service.get_driver') as mock_driver:
        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
        yield mock_driver


@pytest.fixture
def sample_graph_data():
    """Fixture for sample graph data"""
    return {
        "nodes": [
            {"id": "node1", "label": "Stakeholder", "props": {"name": "Test User"}},
            {"id": "node2", "label": "Feature", "props": {"name": "Login"}}
        ],
        "links": [
            {"source": "node1", "target": "node2", "type": "OWNS", "props": {}}
        ]
    }


@pytest.fixture(autouse=True)
def reset_driver():
    """Reset the global driver between tests"""
    import app.services.neo4j_service as service
    service._driver = None
    yield
    service._driver = None
