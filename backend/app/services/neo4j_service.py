# app/services/neo4j_service.py

from typing import Dict, Any, List, Tuple, Iterable, Optional
from neo4j import GraphDatabase, Driver, Transaction
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

# ========= EXISTING FETCH HELPERS (UNCHANGED) =========

def _records_to_graph(rows: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convert Neo4j rows with keys n (node), r (relationship), m (node) into JSON-friendly nodes/links.
    Uses node property 'id' as canonical id.
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
        # IMPORTANT: Use "is not None" for relationships
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
        node_rows = list(s.run(q_nodes, limit=limit))
        rel_rows = list(s.run(q_rels, limit=limit))
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

# ========= ADDITIVE WRITE HELPERS (do not change existing fetch code) =========

# If your project already defines merge_node/merge_relationship elsewhere in this file,
# the adapter will use them; otherwise, these private fallbacks are used internally.

def _fallback_merge_node(tx: Transaction, label: str, node_id: str, props: Dict[str, Any]) -> None:
    if not label or not node_id:
        return
    safe_props = dict(props or {})
    safe_props["id"] = node_id
    query = f"""
    MERGE (n:`{label}` {{ id: $id }})
    ON CREATE SET n += $props, n.createdAt = timestamp()
    ON MATCH  SET n += $props, n.updatedAt = timestamp()
    """
    tx.run(query, id=node_id, props=safe_props)

def _fallback_merge_relationship(
    tx: Transaction,
    rel_type: str,
    source_id: str,
    target_id: str,
    props: Optional[Dict[str, Any]] = None,
) -> None:
    if not rel_type or not source_id or not target_id:
        return
    rel_props = props or {}
    query = f"""
    MATCH (s {{ id: $src_id }}), (t {{ id: $tgt_id }})
    MERGE (s)-[r:`{rel_type}`]->(t)
    ON CREATE SET r += $props, r.createdAt = timestamp()
    ON MATCH  SET r += $props, r.updatedAt = timestamp()
    """
    tx.run(query, src_id=source_id, tgt_id=target_id, props=rel_props)

def _resolve_merge_funcs():
    """
    Use existing merge_node/merge_relationship if defined in this module,
    otherwise use fallbacks defined above.
    """
    gm = globals()
    merge_node_fn = gm.get("merge_node", _fallback_merge_node)
    merge_rel_fn = gm.get("merge_relationship", _fallback_merge_relationship)
    return merge_node_fn, merge_rel_fn

def write_to_db(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Write NER-extracted entities and relationships to Neo4j using MERGE.
    MERGE ensures idempotency: same id won't create duplicates on re-run.
    """
    driver = get_driver()
    entities = data.get("entities", [])
    relationships = data.get("relationships", [])
    
    created_nodes = 0
    created_rels = 0
    
    print(f"📝 Writing to Neo4j: {len(entities)} entities, {len(relationships)} relationships")
    
    with driver.session() as session:
        # 1) MERGE nodes
        for ent in entities:
            ent_id = ent.get("id")
            # FIX: Use "label" from NER output - this is the node type
            ent_label = ent.get("label", "Entity")
            props = ent.get("properties", {})
            
            print(f"  Creating node: id={ent_id}, label={ent_label}, props={props}")
            
            # Build property SET clause
            if props:
                prop_assignments = ", ".join([f"n.{k} = ${k}" for k in props.keys()])
            else:
                prop_assignments = "n.id = $id"  # At minimum, set the id
            
            q = f"""
            MERGE (n:`{ent_label}` {{ id: $id }})
            ON CREATE SET {prop_assignments}
            ON MATCH SET {prop_assignments}
            RETURN n
            """
            
            params = {"id": ent_id, **props}
            result = session.run(q, params)
            print(f"  ✅ Node created/updated: {ent_label} {ent_id}")
            created_nodes += 1
        
        # 2) MERGE relationships
        for rel in relationships:
            src = rel.get("source")
            tgt = rel.get("target")
            rel_type = rel.get("type", "RELATED_TO")
            props = rel.get("properties", {})
            
            print(f"  Creating relationship: {src} -[{rel_type}]-> {tgt}")
            
            # Build property SET clause
            prop_assignments = ", ".join([f"r.{k} = ${k}" for k in props.keys()]) if props else ""
            set_clause = f"ON CREATE SET {prop_assignments}\nON MATCH SET {prop_assignments}" if prop_assignments else ""
            
            q = f"""
            MATCH (a {{ id: $source }}), (b {{ id: $target }})
            MERGE (a)-[r:`{rel_type}`]->(b)
            {set_clause}
            RETURN r
            """
            
            params = {"source": src, "target": tgt, **props}
            session.run(q, params)
            created_rels += 1
    
    print(f"✅ Write complete: {created_nodes} nodes, {created_rels} relationships")
    
    return {
        "nodes_written": created_nodes,
        "relationships_written": created_rels,
        "message": "✅ Entities and relationships written to Neo4j using MERGE"
    }

def fetch_graph_for_recording(recording_id: str, limit: int = 2000) -> Dict[str, Any]:
    """
    Fetch only nodes and relationships that belong to a specific recording/conversation.
    Assumes nodes have a 'recording_id' property set during write.
    """
    q = """
    MATCH (n)
    WHERE n.recording_id = $recording_id
    OPTIONAL MATCH (n)-[r]-(m)
    WHERE m.recording_id = $recording_id
    RETURN n AS n, r AS r, m AS m
    LIMIT $limit
    """
    with get_driver().session() as s:
        rows = list(s.run(q, recording_id=recording_id, limit=limit))
        print((rows))
    nodes, links = _records_to_graph(rows)
    return {"nodes": nodes, "links": links}

def recording_exists_by_audio_id(audio_id: str) -> Optional[str]:
    q = """
    MATCH (n) WHERE n.audio_id = $audio_id
    WITH collect(DISTINCT n.recording_id) AS rids
    RETURN coalesce(head(rids), null) AS recording_id
    """
    with get_driver().session() as s:
        rec = s.run(q, audio_id=audio_id).single()
        return rec["recording_id"] if rec else None
