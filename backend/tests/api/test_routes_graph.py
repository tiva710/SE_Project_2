import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, MagicMock
from app.api.v1.routes_graph import router
from app.models.schemas import GraphResponse

# Create a test app and include the router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestGraphRoutes:
    """Test suite for graph API routes"""
    
    @patch('app.api.v1.routes_graph.fetch_all_graph')
    def test_all_graph_success(self, mock_fetch_all):
        """Test fetching all graph nodes and relationships"""
        # Arrange
        mock_data = {
            "nodes": [
                {"id": "node1", "label": "Stakeholder", "props": {"name": "John"}},
                {"id": "node2", "label": "Feature", "props": {"name": "Login"}}
            ],
            "links": [
                {"source": "node1", "target": "node2", "type": "OWNS", "props": {}}
            ]
        }
        mock_fetch_all.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/all")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_data
        mock_fetch_all.assert_called_once()
    
    @patch('app.api.v1.routes_graph.fetch_all_graph')
    def test_all_graph_with_custom_limit(self, mock_fetch_all):
        """Test fetching all graph with custom limit parameter"""
        # Arrange
        mock_data = {"nodes": [], "links": []}
        mock_fetch_all.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/all?limit=500")
        
        # Assert
        assert response.status_code == 200
        mock_fetch_all.assert_called_once()
    
    @patch('app.api.v1.routes_graph.fetch_same_label_overview')
    def test_stakeholders_overview_success(self, mock_fetch_overview):
        """Test fetching stakeholders overview"""
        # Arrange
        mock_data = {
            "nodes": [
                {"id": "stakeholder.pm", "label": "Stakeholder", "props": {"name": "Project Manager"}},
                {"id": "stakeholder.dev", "label": "Stakeholder", "props": {"name": "Developer"}}
            ],
            "links": [
                {"source": "stakeholder.pm", "target": "stakeholder.dev", "type": "MANAGES", "props": {}}
            ]
        }
        mock_fetch_overview.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/stakeholders/overview")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_data
        mock_fetch_overview.assert_called_once_with("Stakeholder", limit=200)
    
    @patch('app.api.v1.routes_graph.fetch_same_label_overview')
    def test_stakeholders_overview_custom_limit(self, mock_fetch_overview):
        """Test stakeholders overview with custom limit"""
        # Arrange
        mock_data = {"nodes": [], "links": []}
        mock_fetch_overview.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/stakeholders/overview?limit=100")
        
        # Assert
        assert response.status_code == 200
        mock_fetch_overview.assert_called_once_with("Stakeholder", limit=100)
    
    @patch('app.api.v1.routes_graph.fetch_same_label_overview')
    def test_features_overview_success(self, mock_fetch_overview):
        """Test fetching features overview"""
        # Arrange
        mock_data = {
            "nodes": [
                {"id": "feature.checkout", "label": "Feature", "props": {"name": "Checkout"}},
                {"id": "feature.payment", "label": "Feature", "props": {"name": "Payment"}}
            ],
            "links": []
        }
        mock_fetch_overview.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/features/overview")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_data
        mock_fetch_overview.assert_called_once_with("Feature", limit=200)
    
    @patch('app.api.v1.routes_graph.fetch_same_label_neighborhood')
    def test_stakeholder_neighborhood_success(self, mock_fetch_neighborhood):
        """Test fetching stakeholder neighborhood"""
        # Arrange
        mock_data = {
            "nodes": [
                {"id": "stakeholder.pm", "label": "Stakeholder", "props": {"name": "PM"}},
                {"id": "feature.login", "label": "Feature", "props": {"name": "Login"}}
            ],
            "links": [
                {"source": "stakeholder.pm", "target": "feature.login", "type": "REQUESTS", "props": {}}
            ]
        }
        mock_fetch_neighborhood.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/stakeholders/neighborhood?id=stakeholder.pm&k=1&limit=500")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_data
        mock_fetch_neighborhood.assert_called_once_with(
            center_id="stakeholder.pm", 
            label="Stakeholder", 
            k=1, 
            limit=500
        )
    
    @patch('app.api.v1.routes_graph.fetch_same_label_neighborhood')
    def test_stakeholder_neighborhood_not_found(self, mock_fetch_neighborhood):
        """Test stakeholder neighborhood when no nodes found"""
        # Arrange
        mock_data = {"nodes": [], "links": []}
        mock_fetch_neighborhood.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/stakeholders/neighborhood?id=invalid.id")
        
        # Assert
        assert response.status_code == 404
        assert "No nodes found around id=invalid.id" in response.json()["detail"]
    
    @patch('app.api.v1.routes_graph.fetch_same_label_neighborhood')
    def test_stakeholder_neighborhood_with_hops(self, mock_fetch_neighborhood):
        """Test stakeholder neighborhood with multiple hops"""
        # Arrange
        mock_data = {
            "nodes": [{"id": "node1", "label": "Stakeholder", "props": {}}],
            "links": []
        }
        mock_fetch_neighborhood.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/stakeholders/neighborhood?id=stakeholder.pm&k=3")
        
        # Assert
        assert response.status_code == 200
        mock_fetch_neighborhood.assert_called_once_with(
            center_id="stakeholder.pm",
            label="Stakeholder",
            k=3,
            limit=500
        )
    
    @patch('app.api.v1.routes_graph.fetch_same_label_neighborhood')
    def test_feature_neighborhood_success(self, mock_fetch_neighborhood):
        """Test fetching feature neighborhood"""
        # Arrange
        mock_data = {
            "nodes": [
                {"id": "feature.checkout", "label": "Feature", "props": {"name": "Checkout"}},
                {"id": "feature.cart", "label": "Feature", "props": {"name": "Cart"}}
            ],
            "links": [
                {"source": "feature.checkout", "target": "feature.cart", "type": "DEPENDS_ON", "props": {}}
            ]
        }
        mock_fetch_neighborhood.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/features/neighborhood?id=feature.checkout")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_data
        mock_fetch_neighborhood.assert_called_once_with(
            center_id="feature.checkout",
            label="Feature",
            k=1,
            limit=500
        )
    
    @patch('app.api.v1.routes_graph.fetch_same_label_neighborhood')
    def test_feature_neighborhood_not_found(self, mock_fetch_neighborhood):
        """Test feature neighborhood when no nodes found"""
        # Arrange
        mock_data = {"nodes": [], "links": []}
        mock_fetch_neighborhood.return_value = mock_data
        
        # Act
        response = client.get("/api/graph/features/neighborhood?id=nonexistent.feature")
        
        # Assert
        assert response.status_code == 404
        assert "No nodes found" in response.json()["detail"]
    
    def test_stakeholder_neighborhood_missing_id(self):
        """Test stakeholder neighborhood without required id parameter"""
        # Act
        response = client.get("/api/graph/stakeholders/neighborhood")
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_invalid_limit_parameter(self):
        """Test with invalid limit parameter values"""
        # Act - limit too high
        response = client.get("/api/graph/stakeholders/overview?limit=99999")
        
        # Assert
        assert response.status_code == 422
    
    def test_invalid_k_parameter(self):
        """Test with invalid k (hops) parameter"""
        # Act
        response = client.get("/api/graph/stakeholders/neighborhood?id=test&k=10")
        
        # Assert
        assert response.status_code == 422  # k should be between 1 and 5
