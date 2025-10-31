from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import GraphResponse
from app.services.neo4j_service import fetch_same_label_overview, fetch_same_label_neighborhood

router = APIRouter(prefix="/api/graph", tags=["graph"])

# Stakeholders-only graph (nodes and stakeholder-stakeholder edges)
@router.get("/stakeholders/overview", response_model=GraphResponse)
def stakeholders_overview(limit: int = Query(200, ge=1, le=2000)):
    data = fetch_same_label_overview("Stakeholder", limit=limit)
    return GraphResponse(**data)

# Features-only graph (nodes and feature-feature edges, e.g., DEPENDS_ON)
@router.get("/features/overview", response_model=GraphResponse)
def features_overview(limit: int = Query(200, ge=1, le=2000)):
    data = fetch_same_label_overview("Feature", limit=limit)
    return GraphResponse(**data)

# Stakeholder neighborhood around a specific id, keeping original names/types
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

# Feature neighborhood around a specific id, keeping original names/types
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
