from typing import Dict, Any, List, Tuple
from neo4j import GraphDatabase, Driver

NEO4J_URI = "NEO4J_URI"
NEO4J_USER = "NEO4J_USER" 
NEO4J_PASS = "NEO4J_PASS"


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

    for rec in rows:
        n = rec.get("n")
        m = rec.get("m")
        rel = rec.get("r")

        # Add/merge node n by business id
        if n:
            nid = n.get("id")
            if nid and nid not in nodes:
                nodes[nid] = {
                    "id": nid,
                    "label": list(n.labels)[0] if getattr(n, "labels", None) else "",
                    "props": {k: v for k, v in n.items()},
                }

        # Add/merge node m by business id
        if m:
            mid = m.get("id")
            if mid and mid not in nodes:
                nodes[mid] = {
                    "id": mid,
                    "label": list(m.labels)[0] if getattr(m, "labels", None) else "",
                    "props": {k: v for k, v in m.items()},
                }

        # Add link using business ids only when a relationship exists
        if rel and n and m:
            sid = n.get("id")
            tid = m.get("id")
            if sid and tid:
                links.append({
                    "type": type(rel).__name__,
                    "source": sid,   # business id
                    "target": tid,   # business id
                    "props": {k: v for k, v in rel.items()},
                })

    return list(nodes.values()), links

def fetch_same_label_overview(label: str, limit: int = 200) -> Dict[str, Any]:
    # Only nodes with the given label, and only edges where both ends have that label
    q = f"""
    MATCH (n:`{label}`)
    OPTIONAL MATCH (n)-[r]- (m:`{label}`)
    RETURN n, r, m, elementId(startNode(r)) AS start_id, elementId(endNode(r)) AS end_id
    LIMIT $limit
    """
    with get_driver().session() as s:
        rows = list(s.run(q, limit=limit))
        print(rows)
    nodes, links = _to_graph(rows)
    # print(links)
    return {"nodes": nodes, "links": links}

def fetch_same_label_neighborhood(center_id: str, label: str, k: int = 1, limit: int = 500) -> Dict[str, Any]:
    # K-hop neighborhood, but keep only edges where at least one endpoint has the requested label
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
    RETURN s AS n, r AS r, e AS m, elementId(s) AS start_id, elementId(e) AS end_id
    """
    with get_driver().session() as s:
        rows = list(s.run(q, id=center_id, k=k, label=label, limit=limit))
    nodes, links = _to_graph(rows)
    return {"nodes": nodes, "links": links}
