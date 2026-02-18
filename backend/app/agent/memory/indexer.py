"""Auto-indexing for item embeddings."""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.database import async_session_maker
from app.services.embedding_service import embedding_service
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="index_item")
def index_item_task(item_id: str):
    """Celery task wrapper for indexing a single item."""
    import asyncio
    asyncio.run(_index_item(item_id))


async def _index_item(item_id: str):
    """Generate and store embedding for an item."""
    async with async_session_maker() as db:
        try:
            # Fetch item
            stmt = select(Item).where(Item.id == item_id)
            result = await db.execute(stmt)
            item = result.scalar_one_or_none()
            
            if not item:
                logger.warning(f"Item {item_id} not found for indexing")
                return
            
            # Format text for embedding
            text = embedding_service.format_item_for_embedding(
                item_type=item.type,
                title=item.title,
                description=item.description,
                acceptance_criteria=item.acceptance_criteria
            )
            
            # Generate embedding
            embedding = await embedding_service.embed_text(text)
            
            # Update item
            item.embedding = embedding
            await db.commit()
            
            logger.info(f"Successfully indexed item {item_id}")
            
        except Exception as e:
            logger.error(f"Error indexing item {item_id}: {e}")
            await db.rollback()
            raise


@celery_app.task(name="index_all_project_items")
def index_all_project_items_task(project_id: str):
    """Celery task wrapper for indexing all items in a project."""
    import asyncio
    asyncio.run(_index_all_project_items(project_id))


async def _index_all_project_items(project_id: str):
    """Generate embeddings for all items in a project."""
    async with async_session_maker() as db:
        try:
            # Fetch all items in project
            stmt = select(Item).where(Item.project_id == project_id)
            result = await db.execute(stmt)
            items = result.scalars().all()
            
            logger.info(f"Indexing {len(items)} items for project {project_id}")
            
            # Generate embeddings in batch
            texts = [
                embedding_service.format_item_for_embedding(
                    item_type=item.type,
                    title=item.title,
                    description=item.description,
                    acceptance_criteria=item.acceptance_criteria
                )
                for item in items
            ]
            
            embeddings = await embedding_service.embed_batch(texts)
            
            # Update all items
            for item, embedding in zip(items, embeddings):
                item.embedding = embedding
            
            await db.commit()
            
            logger.info(f"Successfully indexed {len(items)} items")
            
        except Exception as e:
            logger.error(f"Error indexing project {project_id}: {e}")
            await db.rollback()
            raise


def trigger_item_indexing(item_id: str):
    """Trigger async indexing for an item."""
    index_item_task.delay(item_id)
    logger.debug(f"Triggered indexing for item {item_id}")
