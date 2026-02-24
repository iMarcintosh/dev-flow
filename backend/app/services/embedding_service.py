"""Embedding service for converting text to vectors."""

import os
from typing import List

from openai import OpenAI


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"
        self.dimensions = 1536

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )

        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []

        response = self.client.embeddings.create(
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
