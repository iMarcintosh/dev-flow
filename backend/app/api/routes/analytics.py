"""
Analytics API Endpoints

Provides usage metrics and statistics for agents.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.services.analytics import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/agents/{agent_id}")
async def get_agent_analytics(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for a specific agent over time.
    
    Query params:
    - days: Number of days to look back (default: 30, max: 365)
    """
    analytics = await analytics_service.get_agent_analytics(
        db=db,
        agent_id=UUID(agent_id),
        user_id=current_user.id,
        days=days
    )
    
    return analytics


@router.get("/agents/{agent_id}/summary")
async def get_agent_summary(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics for an agent.
    
    Returns aggregated metrics like total runs, success rate, avg response time.
    """
    summary = await analytics_service.get_summary_stats(
        db=db,
        agent_id=UUID(agent_id),
        user_id=current_user.id,
        days=days
    )
    
    return summary


@router.get("/agents/{agent_id}/tools")
async def get_agent_tool_usage(
    agent_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tool usage statistics for an agent.
    
    Returns usage count and success rate for each tool.
    """
    tool_stats = await analytics_service.get_tool_usage_stats(
        db=db,
        agent_id=UUID(agent_id),
        user_id=current_user.id,
        days=days
    )
    
    return tool_stats


@router.get("/summary")
async def get_global_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get global analytics summary for the current user.
    
    Aggregates metrics across all agents owned by the user.
    """
    summary = await analytics_service.get_summary_stats(
        db=db,
        user_id=current_user.id,
        days=days
    )
    
    return summary


@router.get("/tools")
async def get_global_tool_usage(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get global tool usage statistics for the current user.
    
    Returns usage across all agents.
    """
    tool_stats = await analytics_service.get_tool_usage_stats(
        db=db,
        user_id=current_user.id,
        days=days
    )
    
    return tool_stats
