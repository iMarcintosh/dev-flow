"""Admin endpoints for system maintenance."""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select, func

from app.database import async_session_maker
from app.models.item import Item
from app.models.user import User
from app.api.routes.auth import get_current_user
from app.agent.memory.indexer import index_item_task, index_all_project_items_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])


@router.get("/embedding-health")
async def check_embedding_health(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Check how many items are missing embeddings.
    
    Returns statistics about embedding coverage across items.
    """
    async with async_session_maker() as db:
        # Total items
        total_stmt = select(func.count(Item.id))
        if project_id:
            total_stmt = total_stmt.where(Item.project_id == UUID(project_id))
        
        result = await db.execute(total_stmt)
        total = result.scalar() or 0
        
        # Items with embeddings
        with_embedding_stmt = select(func.count(Item.id)).where(Item.embedding.isnot(None))
        if project_id:
            with_embedding_stmt = with_embedding_stmt.where(Item.project_id == UUID(project_id))
        
        result = await db.execute(with_embedding_stmt)
        with_embedding = result.scalar() or 0
        
        # Items without embeddings
        missing = total - with_embedding
        health_percentage = (with_embedding / total * 100) if total > 0 else 100
        
        # Get list of items missing embeddings
        missing_items_stmt = select(Item.id, Item.title, Item.project_id).where(Item.embedding.is_(None))
        if project_id:
            missing_items_stmt = missing_items_stmt.where(Item.project_id == UUID(project_id))
        missing_items_stmt = missing_items_stmt.limit(50)  # Limit to first 50
        
        result = await db.execute(missing_items_stmt)
        missing_items = [
            {
                "id": str(item.id),
                "title": item.title,
                "project_id": str(item.project_id)
            }
            for item in result.all()
        ]
        
        return {
            "total_items": total,
            "items_with_embedding": with_embedding,
            "items_missing_embedding": missing,
            "health_percentage": round(health_percentage, 2),
            "status": "healthy" if health_percentage == 100 else "needs_repair",
            "missing_items": missing_items,
            "project_id": project_id
        }


@router.post("/repair-embeddings")
async def repair_embeddings(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Re-index items that are missing embeddings.
    
    - If project_id provided: Only that project
    - If no project_id: All items across all projects (triggers per-project tasks)
    
    Returns the number of items queued for re-indexing.
    """
    async with async_session_maker() as db:
        if project_id:
            # Single project: find missing items
            stmt = select(Item.id).where(
                Item.project_id == UUID(project_id),
                Item.embedding.is_(None)
            )
            result = await db.execute(stmt)
            item_ids = [str(row[0]) for row in result.all()]
            
            if not item_ids:
                return {
                    "success": True,
                    "message": f"All items in project {project_id} already have embeddings",
                    "items_queued": 0,
                    "project_id": project_id
                }
            
            # Queue individual item tasks
            for item_id in item_ids:
                index_item_task.delay(item_id)
            
            logger.info(f"Queued {len(item_ids)} items for re-indexing in project {project_id}")
            
            return {
                "success": True,
                "message": f"Triggered re-indexing for {len(item_ids)} items",
                "items_queued": len(item_ids),
                "project_id": project_id
            }
        
        else:
            # All projects: find projects with missing embeddings
            stmt = select(Item.project_id, func.count(Item.id)).where(
                Item.embedding.is_(None)
            ).group_by(Item.project_id)
            
            result = await db.execute(stmt)
            projects = result.all()
            
            if not projects:
                return {
                    "success": True,
                    "message": "All items across all projects already have embeddings",
                    "projects_queued": 0,
                    "items_queued": 0
                }
            
            # Queue project re-indexing tasks
            total_items = 0
            for project_id, count in projects:
                index_all_project_items_task.delay(str(project_id))
                total_items += count
                logger.info(f"Queued project {project_id} for re-indexing ({count} items)")
            
            return {
                "success": True,
                "message": f"Triggered re-indexing for {len(projects)} projects",
                "projects_queued": len(projects),
                "items_queued": total_items,
                "projects": [
                    {"project_id": str(pid), "missing_count": count}
                    for pid, count in projects
                ]
            }
