from fastapi import APIRouter
from app.models.schemas import ConversationInput, ConversationResponse
from app.services import nlp_service, neo4j_service

router = APIRouter()

@router.post("/conversations", response_model=ConversationResponse)
def process_conversation(convo: ConversationInput):
    entities, relationships = nlp_service.process_conversation(convo.text)
    neo4j_service.add_entities_and_relationships(entities, relationships)
    return {"entities": entities, "relationships": relationships}
