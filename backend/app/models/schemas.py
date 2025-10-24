from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Node(BaseModel):
    id: str
    label: str
    props: Dict[str, Any] = Field(default_factory=dict)

class Link(BaseModel):
    type: str
    source: str
    target: str
    props: Dict[str, Any] = Field(default_factory=dict)

class GraphResponse(BaseModel):
    nodes: List[Node]
    links: List[Link]

class NeighborhoodQuery(BaseModel):
    # Optional center node id; if omitted, returns the overall subgraph for the label
    id: Optional[str] = None
    # Number of hops from the center id; default 1
    k: int = 1
    # Whether to include only relationships among returned nodes
    induced: bool = True

