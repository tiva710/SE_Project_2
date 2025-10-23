from fastapi import FastAPI
from app.api.v1 import routes_conversation, routes_graph, routes_stats, routes_health, routes_transcribe

app = FastAPI(
    title="ReqTrace Graph Backend",
    description="API for conversation, graph, stats, and health endpoints",
    version="1.0.0"
)

# Include routers
app.include_router(routes_conversation.router, prefix="/conversation", tags=["conversation"])
app.include_router(routes_graph.router, prefix="", tags=["graph"])
app.include_router(routes_stats.router, prefix="/stats", tags=["stats"])
app.include_router(routes_health.router, prefix="/health", tags=["health"])
app.include_router(routes_transcribe.router, prefix="/transcript", tags=["transcript"])

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    return {"message": "ReqTrace Graph Backend API is running!"}
