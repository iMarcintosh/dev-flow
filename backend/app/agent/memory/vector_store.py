"""Vector store for semantic search using pgvector."""

import asyncio
import logging
from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from app.models.item import Item
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class VectorStore:
    """Wrapper for pgvector-based semantic search."""
    
    async def index_item(self, db: AsyncSession, item_id: str, api_key: Optional[str] = None):
        """
        Generate and store embedding for an item.
        
        Args:
            db: Database session
            item_id: UUID of the item to index
        """
        from uuid import UUID
        
        # Convert to UUID if string
        if isinstance(item_id, str):
            item_id = UUID(item_id)
        
        # Get the item
        stmt = select(Item).where(Item.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        
        if not item:
            return
        
        # Build text to embed using embedding service for consistent formatting
        text = embedding_service.format_item_for_embedding(
            item_type=item.type.value.upper(),
            title=item.title,
            description=item.description,
            acceptance_criteria=item.acceptance_criteria,
            status=item.status.value,
            priority=item.priority.value
        )
        
        # Generate embedding
        embedding = embedding_service.embed_text(text, api_key=api_key)

        # Update item
        item.embedding = embedding
        await db.commit()
    
    async def similarity_search(
        self,
        db: AsyncSession,
        query: str,
        project_id: str,
        top_k: int = 10,
        api_key: Optional[str] = None
    ) -> List[Item]:
        """
        Find items most similar to the query using cosine similarity.
        
        Args:
            db: Database session
            query: Search query text
            project_id: Filter to specific project
            top_k: Number of results to return
            
        Returns:
            List of most relevant items
        """
        # Generate query embedding (run sync call in thread to avoid blocking event loop)
        try:
            query_embedding = await asyncio.wait_for(
                asyncio.to_thread(lambda: embedding_service.embed_text(query, api_key=api_key)),
                timeout=10.0,
            )
        except Exception as e:
            logger.warning(f"Cannot embed query, skipping semantic search: {e}")
            return []

        # pgvector cosine similarity search
        # <=> operator computes cosine distance (lower is better)
        stmt = (
            select(Item)
            .where(Item.project_id == project_id)
            .where(Item.embedding.isnot(None))
            .order_by(Item.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return list(items)
    
    async def get_project_stats(
        self,
        db: AsyncSession,
        project_id: str
    ) -> dict:
        """Get statistics about items in a project."""
        from uuid import UUID
        from sqlalchemy import func
        from app.models.item import Item
        
        # Convert to UUID if string
        if isinstance(project_id, str):
            project_id = UUID(project_id)
        
        # Get all items for this project
        stmt = select(Item).where(Item.project_id == project_id)
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        # Count by status
        status_counts = {}
        for item in items:
            status = item.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by type
        type_counts = {}
        for item in items:
            item_type = item.type.value
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        # Count by priority
        priority_counts = {}
        for item in items:
            priority = item.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "total_items": len(items),
            "by_status": status_counts,
            "by_type": type_counts,
            "by_priority": priority_counts,
        }


# Singleton instance
vector_store = VectorStore()
