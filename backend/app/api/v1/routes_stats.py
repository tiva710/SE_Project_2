from fastapi import APIRouter
from app.services.neo4j_service import driver

router = APIRouter()

@router.get("/stats")
def graph_stats():
    with driver.session() as session:
        node_count = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
    return {"nodes": node_count, "relationships": rel_count}
