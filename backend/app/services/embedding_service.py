"""Embedding service for converting text to vectors."""

from typing import List, Optional

from openai import OpenAI


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""

    def __init__(self):
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
        self._clients: dict = {}  # cache OpenAI client per key

    def _get_client(self, api_key: Optional[str] = None) -> OpenAI:
        from app.config import settings
        key = api_key or settings.openai_api_key
        if not key:
            raise ValueError("No OpenAI API key available for embeddings")
        if key not in self._clients:
            self._clients[key] = OpenAI(api_key=key)
        return self._clients[key]

    def embed_text(self, text: str, api_key: Optional[str] = None) -> List[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        client = self._get_client(api_key)
        response = client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )

        return response.data[0].embedding

    def embed_batch(self, texts: List[str], api_key: Optional[str] = None) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []

        client = self._get_client(api_key)
        response = client.embeddings.create(
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
