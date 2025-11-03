from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.api.v1 import (
    routes_conversation,
    routes_graph,
    routes_stats,
    routes_health,
    routes_transcribe,
)
# ✅ Explicitly point to backend/.env no matter where uvicorn is started
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
# safety net: remove any system key override
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# --------------------------------------------------------
# Initialize FastAPI
# --------------------------------------------------------
app = FastAPI(
    title="ReqTrace Graph Backend",
    description="API for conversation, graph, stats, and health endpoints",
    version="1.0.0"
)

# --------------------------------------------------------
# ✅ CORS Middleware – allow frontend (localhost:5173)
# --------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------
# Routers
# --------------------------------------------------------
app.include_router(routes_conversation.router, prefix="/conversation", tags=["conversation"])
app.include_router(routes_graph.router, prefix="", tags=["graph"])
# app.include_router(routes_stats.router, prefix="/stats", tags=["stats"])
app.include_router(routes_health.router, prefix="/health", tags=["health"])
app.include_router(routes_transcribe.router, prefix="/transcribe", tags=["transcribe"])

# --------------------------------------------------------
# Root endpoint
# --------------------------------------------------------
@app.get("/", tags=["root"])
async def root():
    return {"message": "ReqTrace Graph Backend API is running!"}