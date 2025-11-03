
# NEO4J_URI = "neo4j+ssc://d31efd7d.databases.neo4j.io"
# NEO4J_USER = "neo4j" 
# NEO4J_PASS = "BT4pSio1PcIf4sm0bDNfx1cZZbB8YzdJJHrQgXB7NHc"

# app/services/neo4j_service.py
from typing import Dict, Any, List, Tuple, Iterable
from neo4j import GraphDatabase, Driver
from pathlib import Path
from dotenv import load_dotenv
import os



load_dotenv(".env")

# Read credentials from environment
NEO4J_URI = os.getenv("NEO4J_URI", "").strip()
NEO4J_USER = os.getenv("NEO4J_USER", "").strip()
NEO4J_PASS = os.getenv("NEO4J_PASS", "").strip()

if not (NEO4J_URI and NEO4J_USER and NEO4J_PASS):
    raise RuntimeError(
        "Missing Neo4j credentials. Ensure NEO4J_URI, NEO4J_USER, NEO4J_PASS are set in your project .env."
    )

_driver: Driver | None = None

def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    return _driver

def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None

from typing import Dict, Any, List, Tuple, Iterable, Set

def _records_to_graph(rows: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convert Neo4j rows with keys n (node), r (relationship), m (node)
    into JSON-friendly nodes/links. Uses node property 'id' as canonical id.
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    links: List[Dict[str, Any]] = []
    
    for rec in rows:
        n = rec.get("n")
        m = rec.get("m")
        r = rec.get("r")
        
        # Node n
        if n:
            nid = n.get("id")
            if nid and nid not in nodes:
                nodes[nid] = {
                    "id": nid,
                    "label": list(n.labels)[0] if getattr(n, "labels", None) else "",
                    "props": {k: v for k, v in n.items()},
                }
        
        # Node m
        if m:
            mid = m.get("id")
            if mid and mid not in nodes:
                nodes[mid] = {
                    "id": mid,
                    "label": list(m.labels)[0] if getattr(m, "labels", None) else "",
                    "props": {k: v for k, v in m.items()},
                }
        
        # Relationship -> link
        # IMPORTANT: Use "is not None" instead of truthiness check
        if r is not None:
            rel_nodes = getattr(r, 'nodes', None)
            if rel_nodes and len(rel_nodes) == 2:
                start_node, end_node = rel_nodes
                
                sid = start_node.get("id") if start_node else None
                tid = end_node.get("id") if end_node else None
                
                if sid and tid:
                    links.append({
                        "type": type(r).__name__,
                        "source": sid,
                        "target": tid,
                        "props": {k: v for k, v in r.items()},
                    })
    
    return list(nodes.values()), links

def fetch_same_label_overview(label: str, limit: int = 200) -> Dict[str, Any]:
    """
    Return nodes with the given label and edges where both endpoints have that label.
    If label is empty or "*", return all nodes and edges.
    """
    if label and label != "*":
        # First query: Get all nodes with the label
        q_nodes = f"""
        MATCH (n:`{label}`)
        RETURN n AS n, null AS r, null AS m
        LIMIT $limit
        """
        
        # Second query: Get all relationships between nodes with the label
        q_rels = f"""
        MATCH (n:`{label}`)-[r]->(m:`{label}`)
        RETURN n AS n, r AS r, m AS m
        LIMIT $limit
        """
    else:
        # Get all nodes
        q_nodes = """
        MATCH (n)
        RETURN n AS n, null AS r, null AS m
        LIMIT $limit
        """
        
        # Get all relationships
        q_rels = """
        MATCH (n)-[r]->(m)
        RETURN n AS n, r AS r, m AS m
        LIMIT $limit
        """
    
    with get_driver().session() as s:
        # Get all nodes first
        node_rows = list(s.run(q_nodes, limit=limit))
        # Get all relationships
        rel_rows = list(s.run(q_rels, limit=limit))
        # Combine them
        all_rows = node_rows + rel_rows
        print(f"Fetched {len(node_rows)} node rows and {len(rel_rows)} relationship rows")
    
    nodes, links = _records_to_graph(all_rows)
    return {"nodes": nodes, "links": links}


def fetch_full_graph(limit: int = 1000) -> Dict[str, Any]:
    """
    Fetch all nodes and all relationships in the graph.
    """
    return fetch_same_label_overview(label="*", limit=limit)


def fetch_same_label_neighborhood(center_id: str, label: str, k: int = 1, limit: int = 500) -> Dict[str, Any]:
    """
    K-hop neighborhood of a center node by id, but keep only edges where at least one
    endpoint has the requested label. If label is empty or "*", include all edges.
    """
    if label and label != "*":
        q = """
        MATCH (c {id:$id})
        CALL {
          WITH c
          MATCH p=(c)-[*..$k]-(x)
          RETURN p LIMIT $limit
        }
        WITH collect(p) AS paths
        WITH apoc.coll.toSet(apoc.coll.flatten([p IN paths | nodes(p)])) AS ns,
             apoc.coll.toSet(apoc.coll.flatten([p IN paths | relationships(p)])) AS rs
        UNWIND ns AS n
        WITH collect(n) AS allNodes, rs
        UNWIND rs AS r
        WITH allNodes, r, startNode(r) AS s, endNode(r) AS e
        WHERE $label IN labels(s) OR $label IN labels(e)
        WITH allNodes, collect({n: s, r: r, m: e}) AS rels
        
        UNWIND allNodes AS node
        RETURN node AS n, null AS r, null AS m
        
        UNION
        
        UNWIND rels AS rel
        RETURN rel.n AS n, rel.r AS r, rel.m AS m
        """
    else:
        q = """
        MATCH (c {id:$id})
        CALL {
          WITH c
          MATCH p=(c)-[*..$k]-(x)
          RETURN p LIMIT $limit
        }
        WITH collect(p) AS paths
        WITH apoc.coll.toSet(apoc.coll.flatten([p IN paths | nodes(p)])) AS ns,
             apoc.coll.toSet(apoc.coll.flatten([p IN paths | relationships(p)])) AS rs
        
        UNWIND ns AS n
        RETURN n AS n, null AS r, null AS m
        
        UNION
        
        UNWIND rs AS r
        RETURN startNode(r) AS n, r AS r, endNode(r) AS m
        """
    
    with get_driver().session() as s:
        rows = list(s.run(q, id=center_id, k=k, label=label, limit=limit))
        print(f"Fetched {len(rows)} rows")
    
    nodes, links = _records_to_graph(rows)
    return {"nodes": nodes, "links": links}

def fetch_all_graph() -> Dict[str, Any]:
    """
    Fetch all nodes and relationships across the entire database.
    Returns nodes of all types and all relationships between them.
    """
    q = """
    MATCH (n)
    OPTIONAL MATCH (n)-[r]-()
    RETURN n AS n, r AS r,
           startNode(r) AS start_node,
           endNode(r) AS end_node
    LIMIT 5000
    """
    with get_driver().session() as s:
        rows = list(s.run(q))
    nodes, links = _records_to_graph(rows)
    return {"nodes": nodes, "links": links}
