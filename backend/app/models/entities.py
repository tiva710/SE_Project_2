from pydantic import BaseModel
from typing import Optional

class Entity(BaseModel):
    id: Optional[str] = None
    name: str
    type: str  # FEATURE | STAKEHOLDER | CONSTRAINT
    confidence: Optional[float] = 1.0
