# from fastapi import APIRouter
# from app.models.schemas import ConversationInput, ConversationResponse
# from app.services import nlp_service, neo4j_service

# router = APIRouter()

# @router.post("/conversations", response_model=ConversationResponse)
# def process_conversation(convo: ConversationInput):
#     entities, relationships = nlp_service.process_conversation(convo.text)
#     neo4j_service.add_entities_and_relationships(entities, relationships)
#     return {"entities": entities, "relationships": relationships}

# app/api/v1/routes_conversation.py

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
import os
import app.services.vector_service as vector_service
from dotenv import load_dotenv
from openai import OpenAI

# ✅ Load environment variables before creating client
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

print(f"✅ Loaded .env from: {os.path.abspath(dotenv_path)}")
print(f"✅ OPENAI_API_KEY starts with: {os.getenv('OPENAI_API_KEY')[:10]}")

# ✅ Initialize OpenAI client using loaded API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()



@router.post("/chat")
async def chat_with_context(payload: dict = Body(...)):
    """
    Handles chat queries using FAISS context + OpenAI (new SDK).
    """
    try:
        query = payload.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query text is required.")

        # 🔍 Retrieve similar transcript chunks from FAISS
        similar_chunks = vector_service.search_similar_transcripts(query)
        context_text = "\n\n".join(
            [chunk["text"] for chunk in similar_chunks]
        )

        # 🧠 Build prompt
        prompt = f"""
        You are a helpful assistant analyzing transcriptions.
        Use the provided context to answer the user's question concisely.
        
        CONTEXT:
        {context_text}

        QUESTION:
        {query}
        """

        # 💬 New OpenAI client interface
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a transcript analysis assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        answer = completion.choices[0].message.content.strip()

        return {
            "query": query,
            "answer": answer,
            "context_used": similar_chunks,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()  # 🔥 prints the full stack trace to your terminal
        raise HTTPException(status_code=500, detail=str(e))

