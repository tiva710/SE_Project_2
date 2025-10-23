from fastapi import APIRouter
from app.services.neo4j_service import driver

router = APIRouter()

@router.get("/graph")
def get_graph():
    with driver.session() as session:
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        result = session.run(query)
        data = []
        for record in result:
            data.append({
                "source": record["n"].get("name") if "name" in record["n"] else None,
                "target": record["m"].get("name") if record["m"] and "name" in record["m"] else None,
                "relationship": record["r"].type if record["r"] else None
            })
    return {"graph": data}

