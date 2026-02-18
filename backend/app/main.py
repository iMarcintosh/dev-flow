from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.api.routes import auth, projects, items, agents, chat, models
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
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "details": str(exc)}
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "devflow-backend"}


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(models.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    logger.info("DevFlow backend starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("DevFlow backend shutting down...")
