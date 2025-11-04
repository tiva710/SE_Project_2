import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Dict, Any
from app.services.neo4j_service import (
    get_driver,
    close_driver,
    _records_to_graph,
    fetch_same_label_overview,
    fetch_full_graph,
    fetch_same_label_neighborhood,
    fetch_all_graph
)


class TestNeo4jDriver:
    """Test suite for Neo4j driver management"""
    
    @patch('app.services.neo4j_service.GraphDatabase')
    def test_get_driver_creates_new_driver(self, mock_graph_db):
        """Test that get_driver creates a new driver instance"""
        # Arrange
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        # Reset the global driver
        import app.services.neo4j_service as service
        service._driver = None
        
        # Act
        driver = get_driver()
        
        # Assert
        assert driver is not None
        mock_graph_db.driver.assert_called_once()
    
    @patch('app.services.neo4j_service.GraphDatabase')
    def test_get_driver_returns_existing_driver(self, mock_graph_db):
        """Test that get_driver returns existing driver if already initialized"""
        # Arrange
        mock_driver = MagicMock()
        import app.services.neo4j_service as service
        service._driver = mock_driver
        
        # Act
        driver = get_driver()
        
        # Assert
        assert driver == mock_driver
        mock_graph_db.driver.assert_not_called()
    
    @patch('app.services.neo4j_service._driver')
    def test_close_driver(self, mock_driver_var):
        """Test closing the Neo4j driver"""
        # Arrange
        mock_driver = MagicMock()
        import app.services.neo4j_service as service
        service._driver = mock_driver
        
        # Act
        close_driver()
        
        # Assert
        mock_driver.close.assert_called_once()


class TestRecordsToGraph:
    """Test suite for _records_to_graph helper function"""
    
    def test_records_to_graph_with_nodes_only(self):
        """Test converting records with only nodes"""
        # Arrange
        mock_node = MagicMock()
        mock_node.get.return_value = "node1"
        mock_node.__getitem__ = lambda self, key: {"id": "node1", "name": "Test"}[key]
        mock_node.items.return_value = [("id", "node1"), ("name", "Test")]
        mock_node.labels = ["Stakeholder"]
        
        records = [{"n": mock_node, "m": None, "r": None}]
        
        # Act
        nodes, links = _records_to_graph(records)
        
        # Assert
        assert len(nodes) == 1
        assert len(links) == 0
        assert nodes[0]["id"] == "node1"
    
    def test_records_to_graph_with_relationships(self):
        """Test converting records with nodes and relationships"""
        # Arrange
        mock_node1 = MagicMock()
        mock_node1.get.return_value = "node1"
        mock_node1.__getitem__ = lambda self, key: {"id": "node1"}[key]
        mock_node1.items.return_value = [("id", "node1")]
        mock_node1.labels = ["Stakeholder"]
        
        mock_node2 = MagicMock()
        mock_node2.get.return_value = "node2"
        mock_node2.__getitem__ = lambda self, key: {"id": "node2"}[key]
        mock_node2.items.return_value = [("id", "node2")]
        mock_node2.labels = ["Feature"]
        
        mock_rel = MagicMock()
        mock_rel.nodes = [mock_node1, mock_node2]
        mock_rel.items.return_value = [("weight", 1.0)]
        type(mock_rel).__name__ = "OWNS"
        
        records = [{"n": mock_node1, "m": mock_node2, "r": mock_rel}]
        
        # Act
        nodes, links = _records_to_graph(records)
        
        # Assert
        assert len(nodes) == 2
        assert len(links) == 1
        assert links[0]["source"] == "node1"
        assert links[0]["target"] == "node2"
        assert links[0]["type"] == "OWNS"
    
    def test_records_to_graph_deduplicates_nodes(self):
        """Test that duplicate nodes are not added multiple times"""
        # Arrange
        mock_node = MagicMock()
        mock_node.get.return_value = "node1"
        mock_node.__getitem__ = lambda self, key: {"id": "node1"}[key]
        mock_node.items.return_value = [("id", "node1")]
        mock_node.labels = ["Stakeholder"]
        
        records = [
            {"n": mock_node, "m": None, "r": None},
            {"n": mock_node, "m": None, "r": None}
        ]
        
        # Act
        nodes, links = _records_to_graph(records)
        
        # Assert
        assert len(nodes) == 1
    
    def test_records_to_graph_empty_records(self):
        """Test converting empty records list"""
        # Arrange
        records = []
        
        # Act
        nodes, links = _records_to_graph(records)
        
        # Assert
        assert len(nodes) == 0
        assert len(links) == 0


class TestFetchSameLabelOverview:
    """Test suite for fetch_same_label_overview function"""
    
    @patch('app.services.neo4j_service.get_driver')
    @patch('app.services.neo4j_service._records_to_graph')
    def test_fetch_same_label_overview_with_label(self, mock_records_to_graph, mock_get_driver):
        """Test fetching overview for specific label"""
        # Arrange
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_session.run.return_value = []
        mock_records_to_graph.return_value = ([{"id": "node1"}], [])
        
        # Act
        result = fetch_same_label_overview("Stakeholder", limit=100)
        
        # Assert
        assert "nodes" in result
        assert "links" in result
        assert mock_session.run.call_count == 2  # Called twice for nodes and relationships
    
    @patch('app.services.neo4j_service.get_driver')
    @patch('app.services.neo4j_service._records_to_graph')
    def test_fetch_same_label_overview_all_labels(self, mock_records_to_graph, mock_get_driver):
        """Test fetching overview for all labels using asterisk"""
        # Arrange
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_session.run.return_value = []
        mock_records_to_graph.return_value = ([], [])
        
        # Act
        result = fetch_same_label_overview("*", limit=200)
        
        # Assert
        assert "nodes" in result
        assert "links" in result
        assert mock_session.run.call_count == 2
    
    @patch('app.services.neo4j_service.get_driver')
    @patch('app.services.neo4j_service._records_to_graph')
    def test_fetch_same_label_overview_respects_limit(self, mock_records_to_graph, mock_get_driver):
        """Test that limit parameter is passed correctly"""
        # Arrange
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_session.run.return_value = []
        mock_records_to_graph.return_value = ([], [])
        
        # Act
        result = fetch_same_label_overview("Feature", limit=50)
        
        # Assert
        calls = mock_session.run.call_args_list
        for call_obj in calls:
            assert call_obj[1]["limit"] == 50


class TestFetchFullGraph:
    """Test suite for fetch_full_graph function"""
    
    @patch('app.services.neo4j_service.fetch_same_label_overview')
    def test_fetch_full_graph(self, mock_fetch_overview):
        """Test fetching full graph delegates to fetch_same_label_overview"""
        # Arrange
        expected_result = {"nodes": [], "links": []}
        mock_fetch_overview.return_value = expected_result
        
        # Act
        result = fetch_full_graph(limit=500)
        
        # Assert
        assert result == expected_result
        mock_fetch_overview.assert_called_once_with(label="*", limit=500)


class TestFetchSameLabelNeighborhood:
    """Test suite for fetch_same_label_neighborhood function"""
    
    @patch('app.services.neo4j_service.get_driver')
    @patch('app.services.neo4j_service._records_to_graph')
    def test_fetch_neighborhood_with_specific_label(self, mock_records_to_graph, mock_get_driver):
        """Test fetching neighborhood for specific label"""
        # Arrange
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_session.run.return_value = []
        mock_records_to_graph.return_value = ([{"id": "center"}], [])
        
        # Act
        result = fetch_same_label_neighborhood("center.id", "Stakeholder", k=2, limit=300)
        
        # Assert
        assert "nodes" in result
        assert "links" in result
        mock_session.run.assert_called_once()
        
        call_args = mock_session.run.call_args
        assert call_args[1]["id"] == "center.id"
        assert call_args[1]["k"] == 2
        assert call_args[1]["label"] == "Stakeholder"
        assert call_args[1]["limit"] == 300
    
    @patch('app.services.neo4j_service.get_driver')
    @patch('app.services.neo4j_service._records_to_graph')
    def test_fetch_neighborhood_all_labels(self, mock_records_to_graph, mock_get_driver):
        """Test fetching neighborhood for all labels"""
        # Arrange
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_session.run.return_value = []
        mock_records_to_graph.return_value = ([], [])
        
        # Act
        result = fetch_same_label_neighborhood("node.id", "*", k=1)
        
        # Assert
        assert "nodes" in result
        call_args = mock_session.run.call_args
        assert call_args[1]["id"] == "node.id"
    
    @patch('app.services.neo4j_service.get_driver')
    @patch('app.services.neo4j_service._records_to_graph')
    def test_fetch_neighborhood_multiple_hops(self, mock_records_to_graph, mock_get_driver):
        """Test fetching neighborhood with multiple hops"""
        # Arrange
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_session.run.return_value = []
        mock_records_to_graph.return_value = ([], [])
        
        # Act
        result = fetch_same_label_neighborhood("node.id", "Feature", k=3)
        
        # Assert
        call_args = mock_session.run.call_args
        assert call_args[1]["k"] == 3


class TestFetchAllGraph:
    """Test suite for fetch_all_graph function"""
    
    @patch('app.services.neo4j_service.get_driver')
    @patch('app.services.neo4j_service._records_to_graph')
    def test_fetch_all_graph(self, mock_records_to_graph, mock_get_driver):
        """Test fetching entire graph database"""
        # Arrange
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_session.run.return_value = []
        mock_records_to_graph.return_value = ([{"id": "n1"}, {"id": "n2"}], [{"source": "n1", "target": "n2"}])
        
        # Act
        result = fetch_all_graph()
        
        # Assert
        assert "nodes" in result
        assert "links" in result
        assert len(result["nodes"]) == 2
        assert len(result["links"]) == 1
        mock_session.run.assert_called_once()


class TestErrorHandling:
    """Test suite for error handling scenarios"""
    
    @patch('app.services.neo4j_service.get_driver')
    def test_fetch_same_label_overview_connection_error(self, mock_get_driver):
        """Test handling of database connection errors"""
        # Arrange
        mock_get_driver.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            fetch_same_label_overview("Stakeholder")
        
        assert "Connection failed" in str(exc_info.value)
    
    @patch('app.services.neo4j_service.get_driver')
    def test_fetch_neighborhood_query_error(self, mock_get_driver):
        """Test handling of query execution errors"""
        # Arrange
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver
        
        mock_session.run.side_effect = Exception("Query execution failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            fetch_same_label_neighborhood("invalid.id", "Stakeholder")
        
        assert "Query execution failed" in str(exc_info.value)
