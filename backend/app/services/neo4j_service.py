from typing import Dict, Any, List, Tuple
from neo4j import GraphDatabase, Driver


NEO4J_URI = "URI"
NEO4J_USER = "neo4j" 
NEO4J_PASS = "pwd"

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

def _to_graph(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    nodes: Dict[str, Dict[str, Any]] = {}
    links: List[Dict[str, Any]] = []
    for r in rows:
        n = r.get("n")
        m = r.get("m")
        rel = r.get("r")
        if n:
            nid = n.get("id")
            if nid and nid not in nodes:
                nodes[nid] = {
                    "id": nid,
                    "label": list(n.labels)[0] if n.labels else "",
                    "props": {k: v for k, v in n.items()},
                }
        if m:
            mid = m.get("id")
            if mid and mid not in nodes:
                nodes[mid] = {
                    "id": mid,
                    "label": list(m.labels)[0] if m.labels else "",
                    "props": {k: v for k, v in m.items()},
                }
        if rel:
            links.append({
                "type": type(rel).__name__,
                "source": r["start_id"],
                "target": r["end_id"],
                "props": {k: v for k, v in rel.items()},
            })
    return list(nodes.values()), links

def fetch_same_label_overview(label: str, limit: int = 200) -> Dict[str, Any]:
    q = f"""
    MATCH (n:`{label}`)
    MATCH p=(n)-[r]-(:`{label}`)
    RETURN p
    LIMIT $limit
    """
    with get_driver().session() as s:
        rows = list(s.run(q, limit=limit))
    # Expand paths to n,r,m and start/end ids so your _to_graph works unchanged
    expanded = []
    for rec in rows:
        p = rec["p"]
        for r in p.relationships:
            s_node = r.start_node
            e_node = r.end_node
            expanded.append({
                "n": s_node,
                "m": e_node,
                "r": r,
                "start_id": s_node.element_id,
                "end_id": e_node.element_id,
            })
    nodes, links = _to_graph(expanded)
    return {"nodes": nodes, "links": links}


def fetch_same_label_neighborhood(center_id: str, label: str, k: int = 1, limit: int = 500) -> Dict[str, Any]:
    # Try APOC first (if available); otherwise fall back
    q_apoc = """
    MATCH (c {id:$id})
    CALL {
      WITH c
      MATCH p=(c)-[*..$k]-(x)
      RETURN p LIMIT $limit
    }
    RETURN p
    """
    q_fallback = """
    MATCH (c {id:$id})
    MATCH p=(c)-[*..$k]-(x)
    RETURN p
    LIMIT $limit
    """
    with get_driver().session() as s:
        try:
            rows = list(s.run(q_apoc, id=center_id, k=k, limit=limit))
            if not rows:
                rows = list(s.run(q_fallback, id=center_id, k=k, limit=limit))
        except Exception:
            rows = list(s.run(q_fallback, id=center_id, k=k, limit=limit))

    # Expand paths, then filter edges so at least one endpoint has the requested label
    expanded = []
    for rec in rows:
        p = rec["p"]
        for r in p.relationships:
            s_node = r.start_node
            e_node = r.end_node
            if label in list(s_node.labels) or label in list(e_node.labels):
                expanded.append({
                    "n": s_node,
                    "m": e_node,
                    "r": r,
                    "start_id": s_node.element_id,
                    "end_id": e_node.element_id,
                })
    nodes, links = _to_graph(expanded)
    return {"nodes": nodes, "links": links}

