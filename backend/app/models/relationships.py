from pydantic import BaseModel

class Relationship(BaseModel):
    source: str
    target: str
    type: str  # DEPENDS_ON | IMPACTS | CONTAINS | CONFLICTS_WITH
    confidence: float = 1.0
