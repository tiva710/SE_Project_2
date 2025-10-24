from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def extract_entities_and_relationships(text: str):
    prompt = f"""
    You are a requirements engineer. Extract the following from the conversation:
    - Entities: features, stakeholders, constraints
    - Relationships: DEPENDS_ON, IMPACTS, CONTAINS, CONFLICTS_WITH
    Return JSON with keys: entities and relationships.
    Text: {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Extract structured information."},
                  {"role": "user", "content": prompt}]
    )

    try:
        result = response.choices[0].message.content
        return result
    except Exception as e:
        print("Error:", e)
        return {"entities": [], "relationships": []}
