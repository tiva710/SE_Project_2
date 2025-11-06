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

# =========================
# Write helpers and adapter
# =========================

import builtins
import types
import app.services.neo4j_service as svc
from unittest.mock import MagicMock, patch


class TestFallbackMergeNode:
    def test_fallback_merge_node_builds_query_and_props(self):
        tx = MagicMock()
        props = {"name": "Alice", "role": "PM"}

        # Call
        svc._fallback_merge_node(tx, label="Stakeholder", node_id="stakeholder.alice", props=props)

        # Assert cypher + params
        assert tx.run.call_count == 1
        cypher = tx.run.call_args.args[0]
        params = tx.run.call_args.kwargs
        assert "MERGE (n:`Stakeholder` { id: $id })" in cypher
        assert "ON CREATE SET n += $props" in cypher
        assert "ON MATCH SET n += $props" in cypher
        assert params["id"] == "stakeholder.alice"
        assert params["props"]["id"] == "stakeholder.alice"
        assert params["props"]["name"] == "Alice"
        assert params["props"]["role"] == "PM"

    def test_fallback_merge_node_skips_when_missing_label_or_id(self):
        tx = MagicMock()

        svc._fallback_merge_node(tx, label="", node_id="n1", props={})
        svc._fallback_merge_node(tx, label=None, node_id="n1", props={})
        svc._fallback_merge_node(tx, label="Stakeholder", node_id="", props={})
        svc._fallback_merge_node(tx, label="Stakeholder", node_id=None, props={})

        tx.run.assert_not_called()


class TestFallbackMergeRelationship:
    def test_fallback_merge_relationship_builds_query_and_props(self):
        tx = MagicMock()
        rprops = {"since": 2024, "weight": 0.7}

        svc._fallback_merge_relationship(
            tx, rel_type="OWNS", source_id="s1", target_id="t1", props=rprops
        )

        assert tx.run.call_count == 1
        cypher = tx.run.call_args.args[0]
        params = tx.run.call_args.kwargs
        assert "MATCH (s { id: $src_id }), (t { id: $tgt_id })" in cypher
        assert "MERGE (s)-[r:`OWNS`]->(t)" in cypher
        assert "ON CREATE SET r += $props" in cypher
        assert "ON MATCH SET r += $props" in cypher
        assert params["src_id"] == "s1"
        assert params["tgt_id"] == "t1"
        assert params["props"]["since"] == 2024
        assert params["props"]["weight"] == 0.7

    def test_fallback_merge_relationship_skips_when_missing_fields(self):
        tx = MagicMock()

        svc._fallback_merge_relationship(tx, rel_type="", source_id="s1", target_id="t1", props={})
        svc._fallback_merge_relationship(tx, rel_type=None, source_id="s1", target_id="t1", props={})
        svc._fallback_merge_relationship(tx, rel_type="OWNS", source_id="", target_id="t1", props={})
        svc._fallback_merge_relationship(tx, rel_type="OWNS", source_id="s1", target_id="", props={})

        tx.run.assert_not_called()


class TestResolveMergeFuncs:
    def test_resolve_merge_funcs_uses_fallbacks_by_default(self, monkeypatch):
        # Ensure globals don't have custom functions
        monkeypatch.setitem(svc.globals(), "merge_node", None) if "merge_node" in svc.globals() else None
        monkeypatch.setitem(svc.globals(), "merge_relationship", None) if "merge_relationship" in svc.globals() else None
        # Resolve
        node_fn, rel_fn = svc._resolve_merge_funcs()
        assert node_fn.__name__ == "_fallback_merge_node"
        assert rel_fn.__name__ == "_fallback_merge_relationship"

    def test_resolve_merge_funcs_prefers_global_functions(self, monkeypatch):
        def custom_merge_node(tx, label, node_id, props):
            return "node_custom"

        def custom_merge_relationship(tx, rel_type, source_id, target_id, props=None):
            return "rel_custom"

        monkeypatch.setitem(svc.globals(), "merge_node", custom_merge_node)
        monkeypatch.setitem(svc.globals(), "merge_relationship", custom_merge_relationship)

        node_fn, rel_fn = svc._resolve_merge_funcs()
        assert node_fn is custom_merge_node
        assert rel_fn is custom_merge_relationship

        # Cleanup: restore to fallbacks to avoid side‑effects on other tests
        monkeypatch.setitem(svc.globals(), "merge_node", svc._fallback_merge_node)
        monkeypatch.setitem(svc.globals(), "merge_relationship", svc._fallback_merge_relationship)


class TestWriteToDb:
    @patch("app.services.neo4j_service.get_driver")
    def test_write_to_db_happy_path_single_transaction_and_counts(self, mock_get_driver):
        mock_session = MagicMock()
        mock_tx = MagicMock()

        def execute_write(fn):
            fn(mock_tx)

        mock_session.execute_write.side_effect = execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver

        payload = {
            "entities": [
                {"id": "s1", "label": "Stakeholder", "properties": {"name": "Alice"}},
                {"id": "f1", "label": "Feature", "properties": {"name": "Login"}},
            ],
            "relationships": [
                {"source": "s1", "target": "f1", "type": "OWNS", "properties": {"since": 2024}}
            ],
        }

        result = svc.write_to_db(payload)

        assert result == {"nodes_written": 2, "relationships_written": 1}
        assert mock_session.execute_write.call_count == 1
        # 2 node merges + 1 rel merge
        assert mock_tx.run.call_count == 3

    @patch("app.services.neo4j_service.get_driver")
    def test_write_to_db_skips_invalid_entities_and_rels(self, mock_get_driver):
        mock_session = MagicMock()
        mock_tx = MagicMock()

        def execute_write(fn):
            fn(mock_tx)

        mock_session.execute_write.side_effect = execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver

        payload = {
            "entities": [
                {"id": "", "label": "Stakeholder", "properties": {}},             # skip
                {"id": "x1", "label": "", "properties": {}},                      # skip
                {"id": "ok1", "label": "Stakeholder", "properties": {"n": 1}},    # keep
            ],
            "relationships": [
                {"source": "", "target": "t", "type": "OWNS", "properties": {}},  # skip
                {"source": "s", "target": "", "type": "OWNS", "properties": {}},  # skip
                {"source": "s", "target": "t", "type": "", "properties": {}},     # skip
                {"source": "s", "target": "t", "type": "OWNS", "properties": {}}, # keep
            ],
        }

        result = svc.write_to_db(payload)

        assert result == {"nodes_written": 1, "relationships_written": 1}
        assert mock_tx.run.call_count == 2

    @patch("app.services.neo4j_service.get_driver")
    def test_write_to_db_handles_non_dict_payload(self, mock_get_driver):
        # Minimal driver/session; should not be used
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver

        result_none = svc.write_to_db(None)
        result_list = svc.write_to_db([])
        result_str = svc.write_to_db("not a dict")

        assert result_none == {"nodes_written": 0, "relationships_written": 0}
        assert result_list == {"nodes_written": 0, "relationships_written": 0}
        assert result_str == {"nodes_written": 0, "relationships_written": 0}
        mock_session.execute_write.assert_not_called()

    @patch("app.services.neo4j_service.get_driver")
    def test_write_to_db_uses_custom_merge_functions_when_present(self, mock_get_driver, monkeypatch):
        mock_session = MagicMock()
        mock_tx = MagicMock()

        def execute_write(fn):
            fn(mock_tx)

        mock_session.execute_write.side_effect = execute_write
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver

        invoked = {"node": 0, "rel": 0}

        def custom_merge_node(tx, label, node_id, props):
            invoked["node"] += 1
            assert label == "Stakeholder"
            assert node_id == "s1"
            assert props["id"] == "s1"
            assert props["name"] == "Alice"

        def custom_merge_relationship(tx, rel_type, source_id, target_id, props=None):
            invoked["rel"] += 1
            assert rel_type == "OWNS"
            assert source_id == "s1"
            assert target_id == "f1"
            assert props["since"] == 2024

        # Patch globals so resolver picks these
        monkeypatch.setitem(svc.globals(), "merge_node", custom_merge_node)
        monkeypatch.setitem(svc.globals(), "merge_relationship", custom_merge_relationship)

        payload = {
            "entities": [{"id": "s1", "label": "Stakeholder", "properties": {"name": "Alice"}}],
            "relationships": [{"source": "s1", "target": "f1", "type": "OWNS", "properties": {"since": 2024}}],
        }

        result = svc.write_to_db(payload)

        assert result == {"nodes_written": 1, "relationships_written": 1}
        assert invoked["node"] == 1
        assert invoked["rel"] == 1
        # Fallback tx.run should not be called in this path
        assert mock_tx.run.call_count == 0

        # Cleanup: restore to fallbacks
        monkeypatch.setitem(svc.globals(), "merge_node", svc._fallback_merge_node)
        monkeypatch.setitem(svc.globals(), "merge_relationship", svc._fallback_merge_relationship)

    @patch("app.services.neo4j_service.get_driver")
    def test_write_to_db_propagates_transaction_exception(self, mock_get_driver):
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_get_driver.return_value = mock_driver

        def explode(_fn):
            raise RuntimeError("tx failed")

        mock_session.execute_write.side_effect = explode

        with pytest.raises(RuntimeError) as exc:
            svc.write_to_db({"entities": [], "relationships": []})

        assert "tx failed" in str(exc.value)
