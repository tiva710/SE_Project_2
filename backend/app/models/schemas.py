from pydantic import BaseModel
from typing import List, Optional

class Entity(BaseModel):
    id: Optional[str] = None
    name: str
    type: str
    confidence: Optional[float] = 1.0

class Relationship(BaseModel):
    source: str
    target: str
    type: str
    confidence: float = 1.0

class ConversationInput(BaseModel):
    text: str

class ConversationResponse(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]
