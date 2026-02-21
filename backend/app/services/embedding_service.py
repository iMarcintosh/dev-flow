"""Embedding service for converting text to vectors."""

import os
from typing import List
import random


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.use_mock = not api_key or api_key.startswith("sk-proj-xxx")
        
        if not self.use_mock:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
        
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if self.use_mock:
            # Generate deterministic mock embedding based on text hash
            random.seed(hash(text) % (2**32))
            return [random.random() for _ in range(self.dimensions)]
        
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []
        
        if self.use_mock:
            # Generate deterministic mock embeddings
            return [await self.embed_text(t) for t in valid_texts]
        
        response = await self.client.embeddings.create(
            model=self.model,
            input=valid_texts,
            encoding_format="float"
        )
        
        return [data.embedding for data in response.data]
    
    def format_item_for_embedding(
        self,
        item_type: str,
        title: str,
        description: str | None = None,
        acceptance_criteria: str | None = None,
        status: str | None = None,
        priority: str | None = None
    ) -> str:
        """Format item fields into a single text for embedding."""
        parts = [f"{item_type}: {title}"]

        if status:
            parts.append(f"Status: {status}")

        if priority:
            parts.append(f"Priority: {priority}")

        if description:
            parts.append(description)

        if acceptance_criteria:
            parts.append(f"Acceptance Criteria: {acceptance_criteria}")

        return "\n".join(parts)


# Singleton instance
embedding_service = EmbeddingService()

