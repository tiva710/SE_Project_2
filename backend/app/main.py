from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import routes_conversation, routes_graph, routes_stats, routes_health

app = FastAPI(
    title="ReqTrace Graph Backend",
    description="API for conversation, graph, stats, and health endpoints",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include routers
# app.include_router(routes_conversation.router, prefix="/conversation", tags=["conversation"])
app.include_router(routes_graph.router, prefix="", tags=["graph"])
# app.include_router(routes_stats.router, prefix="/stats", tags=["stats"])
app.include_router(routes_health.router, prefix="/health", tags=["health"])

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    return {"message": "ReqTrace Graph Backend API is running!"}
