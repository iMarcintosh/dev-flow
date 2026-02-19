#!/usr/bin/env python3
"""
Re-index all items that are missing embeddings.

Usage:
    python scripts/reindex_all_items.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from app.database import async_session_maker
from app.models.item import Item
from app.agent.memory.indexer import index_all_project_items_task


async def main():
    """Find all projects and trigger re-indexing."""
    async with async_session_maker() as db:
        # Get unique project IDs
        stmt = select(Item.project_id).distinct()
        result = await db.execute(stmt)
        project_ids = result.scalars().all()
        
        print(f"Found {len(project_ids)} projects")
        
        # Get count of items without embeddings per project
        for project_id in project_ids:
            # Count total items in project
            total_stmt = select(func.count(Item.id)).where(
                Item.project_id == project_id
            )
            total = (await db.execute(total_stmt)).scalar()
            
            # Count items without embeddings
            missing_stmt = select(func.count(Item.id)).where(
                Item.project_id == project_id,
                Item.embedding == None
            )
            missing = (await db.execute(missing_stmt)).scalar()
            
            print(f"\nProject {project_id}:")
            print(f"  Total items: {total}")
            print(f"  Missing embeddings: {missing}")
            
            if missing > 0:
                # Trigger reindexing for entire project
                task_result = index_all_project_items_task.delay(str(project_id))
                print(f"  ✓ Triggered reindexing (task: {task_result.id})")
            else:
                print(f"  ✓ All items have embeddings")
        
        print("\n" + "=" * 60)
        print("Reindexing tasks triggered!")
        print("Check Celery worker logs to monitor progress:")
        print("  docker compose logs celery_worker --follow")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
