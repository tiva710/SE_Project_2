
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

        # Relationship -> link (only when both endpoints exist and have business ids)
        if r and n and m:
            sid = n.get("id")
            tid = m.get("id")
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
    """
    q = f"""
    MATCH (n:`{label}`)
    OPTIONAL MATCH (n)-[r]- (m:`{label}`)
    WITH n, r, m
    RETURN n AS n, r AS r, m AS m,
           elementId(startNode(r)) AS start_id,
           elementId(endNode(r))   AS end_id
    LIMIT $limit
    """
    with get_driver().session() as s:
        rows = list(s.run(q, limit=limit))
    nodes, links = _records_to_graph(rows)
    return {"nodes": nodes, "links": links}

def fetch_same_label_neighborhood(center_id: str, label: str, k: int = 1, limit: int = 500) -> Dict[str, Any]:
    """
    K-hop neighborhood of a center node by id, but keep only edges where at least one
    endpoint has the requested label.
    """
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
    UNWIND rs AS r
    WITH ns, r, startNode(r) AS s, endNode(r) AS e
    WHERE $label IN labels(s) OR $label IN labels(e)
    RETURN s AS n, r AS r, e AS m,
           elementId(s) AS start_id,
           elementId(e) AS end_id
    """
    with get_driver().session() as s:
        rows = list(s.run(q, id=center_id, k=k, label=label, limit=limit))
    nodes, links = _records_to_graph(rows)
    return {"nodes": nodes, "links": links}
