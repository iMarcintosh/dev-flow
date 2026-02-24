"""Auto-indexing for item embeddings."""

import logging
from sqlalchemy.orm import Session

from app.models.item import Item
from app.database import SessionLocal  # Sync session for Celery
from app.services.embedding_service import embedding_service
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="index_item")
def index_item_task(item_id: str):
    """Celery task for indexing a single item (synchronous)."""
    db = SessionLocal()
    try:
        # Fetch item
        item = db.query(Item).filter(Item.id == item_id).first()
        
        if not item:
            logger.warning(f"Item {item_id} not found for indexing")
            return
        
        # Format text for embedding
        text = embedding_service.format_item_for_embedding(
            item_type=item.type,
            title=item.title,
            description=item.description,
            acceptance_criteria=item.acceptance_criteria,
            status=item.status.value,
            priority=item.priority.value
        )
        
        # Generate embedding
        embedding = embedding_service.embed_text(text)
        
        # Update item
        item.embedding = embedding
        db.commit()
        
        logger.info(f"✓ Successfully indexed item {item_id}")
        
    except Exception as e:
        logger.error(f"✗ Error indexing item {item_id}: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="index_all_project_items")
def index_all_project_items_task(project_id: str):
    """Celery task for indexing all items in a project (synchronous)."""
    db = SessionLocal()
    try:
        # Fetch all items in project
        items = db.query(Item).filter(Item.project_id == project_id).all()
        
        logger.info(f"Indexing {len(items)} items for project {project_id}")
        
        # Generate embeddings in batch
        texts = [
            embedding_service.format_item_for_embedding(
                item_type=item.type,
                title=item.title,
                description=item.description,
                acceptance_criteria=item.acceptance_criteria,
                status=item.status.value,
                priority=item.priority.value
            )
            for item in items
        ]
        
        # Generate embeddings
        embeddings = embedding_service.embed_batch(texts)
        
        # Update all items
        for item, embedding in zip(items, embeddings):
            item.embedding = embedding
        
        db.commit()
        
        logger.info(f"✓ Successfully indexed {len(items)} items")
        
    except Exception as e:
        logger.error(f"✗ Error indexing project {project_id}: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


def trigger_item_indexing(item_id: str):
    """Trigger async indexing for an item."""
    index_item_task.delay(item_id)
    logger.debug(f"Triggered indexing for item {item_id}")


