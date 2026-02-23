from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.api.routes import auth, projects, items, agents, chat, models, api_keys, custom_agents, agent_chat, teams, admin, tools
import logging

# Import agents to trigger registration
from app.agent.agents import task_creator, chat_agent, daily_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DevFlow API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    response = JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "details": str(exc)}
    )
    origin = request.headers.get("origin")
    if origin and origin in settings.backend_cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "devflow-backend"}


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(tools.router, prefix="/api")
app.include_router(models.router)
app.include_router(chat.router)
app.include_router(api_keys.router)
app.include_router(custom_agents.router)
app.include_router(agent_chat.router)
app.include_router(teams.router)

from app.api.routes import knowledge_base, websocket, analytics, notes
app.include_router(knowledge_base.router)
app.include_router(websocket.router)
app.include_router(analytics.router)
app.include_router(notes.router)


@app.on_event("startup")
async def startup_event():
    logger.info("DevFlow backend starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("DevFlow backend shutting down...")
