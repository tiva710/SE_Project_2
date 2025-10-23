import spacy
import json
from app.services.llm_service import extract_entities_and_relationships

nlp = spacy.load("en_core_web_sm")

def process_conversation(text: str):
    doc = nlp(text)
    llm_result = extract_entities_and_relationships(text)

    try:
        data = json.loads(llm_result)
        entities = data.get("entities", [])
        relationships = data.get("relationships", [])
        return entities, relationships
    except json.JSONDecodeError:
        return [], []
