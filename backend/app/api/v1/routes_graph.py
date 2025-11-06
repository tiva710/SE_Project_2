from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import GraphResponse
from app.services.neo4j_service import (
    fetch_same_label_overview,
    fetch_same_label_neighborhood,
    fetch_all_graph,
)

router = APIRouter(prefix="/api/graph", tags=["graph"])

# All nodes and relationships across the entire database
@router.get("/all", response_model=GraphResponse)
def all_graph(limit: int = Query(5000, ge=100, le=10000)):
    """
    Fetch all nodes and relationships across the entire graph database.
    """
    data = fetch_all_graph()
    return GraphResponse(**data)

# Stakeholders-only graph
@router.get("/stakeholders/overview", response_model=GraphResponse)
def stakeholders_overview(limit: int = Query(200, ge=1, le=2000)):
    data = fetch_same_label_overview("Stakeholder", limit=limit)
    return GraphResponse(**data)

# Features-only graph
@router.get("/features/overview", response_model=GraphResponse)
def features_overview(limit: int = Query(200, ge=1, le=2000)):
    data = fetch_same_label_overview("Feature", limit=limit)
    return GraphResponse(**data)

# Stakeholder neighborhood
@router.get("/stakeholders/neighborhood", response_model=GraphResponse)
def stakeholder_neighborhood(
    id: str = Query(..., description="Center node id, e.g., stakeholder.pm"),
    k: int = Query(1, ge=1, le=5),
    limit: int = Query(500, ge=10, le=5000),
):
    data = fetch_same_label_neighborhood(center_id=id, label="Stakeholder", k=k, limit=limit)
    if not data["nodes"]:
        raise HTTPException(status_code=404, detail=f"No nodes found around id={id}")
    return GraphResponse(**data)

# Feature neighborhood
@router.get("/features/neighborhood", response_model=GraphResponse)
def feature_neighborhood(
    id: str = Query(..., description="Center node id, e.g., feature.checkout"),
    k: int = Query(1, ge=1, le=5),
    limit: int = Query(500, ge=10, le=5000),
):
    data = fetch_same_label_neighborhood(center_id=id, label="Feature", k=k, limit=limit)
    if not data["nodes"]:
        raise HTTPException(status_code=404, detail=f"No nodes found around id={id}")
    return GraphResponse(**data)

@router.get("/conversation/{conversation_id}", response_model=GraphResponse)
def conversation_graph(conversation_id: str, limit: int = Query(2000, ge=1, le=10000)):
    """
    Fetch graph scoped to a specific conversation/recording ID.
    Returns only nodes and relationships tagged with that recording_id.
    """
    from app.services.neo4j_service import fetch_graph_for_recording
    
    data = fetch_graph_for_recording(conversation_id, limit=limit)
    if not data["nodes"]:
        raise HTTPException(
            status_code=404, 
            detail=f"No nodes found for conversation {conversation_id}"
        )
    return GraphResponse(**data)
