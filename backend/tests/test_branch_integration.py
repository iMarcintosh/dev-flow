"""Regression checks for the merged per-user embedding and model-cache changes.

Run with: python -m unittest discover -s tests -v
Provider clients are mocked; these checks never send credentials or API requests.
"""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.api.routes import models


class EmbeddingIntegrationTests(unittest.TestCase):
    def test_missing_key_does_not_prevent_initialization(self):
        with patch.object(settings, "openai_api_key", None):
            service = EmbeddingService()
            self.assertEqual(service.embed_batch([]), [])
            with self.assertRaisesRegex(ValueError, "No OpenAI API key"):
                service.embed_text("A note")

    def test_users_have_separate_clients_and_explicit_keys_take_precedence(self):
        clients = {}

        def client_for_key(*, api_key):
            client = MagicMock()
            client.embeddings.create.return_value = SimpleNamespace(
                data=[SimpleNamespace(embedding=[1.0, 2.0])]
            )
            clients[api_key] = client
            return client

        with patch.object(settings, "openai_api_key", "global-test-fixture"), patch(
            "app.services.embedding_service.OpenAI", side_effect=client_for_key
        ) as factory:
            service = EmbeddingService()
            self.assertEqual(service.embed_text("First", api_key="user-a-fixture"), [1.0, 2.0])
            service.embed_batch(["Second"], api_key="user-b-fixture")
            service.embed_text("Again", api_key="user-a-fixture")
            self.assertEqual(factory.call_count, 2)
            self.assertEqual(clients["user-a-fixture"].embeddings.create.call_count, 2)
            self.assertEqual(clients["user-b-fixture"].embeddings.create.call_count, 1)
            self.assertNotIn("global-test-fixture", clients)

    def test_global_fallback_remains_available(self):
        with patch.object(settings, "openai_api_key", "global-test-fixture"), patch(
            "app.services.embedding_service.OpenAI"
        ) as factory:
            EmbeddingService()._get_client()
            factory.assert_called_once_with(api_key="global-test-fixture")


class ModelCacheIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cache_and_provider_keys_are_scoped_to_each_user(self):
        cache = {}

        async def cache_get(key):
            return cache.get(key)

        async def cache_set(key, value, ex):
            cache[key] = value

        async def user_key(db, user_id, provider):
            return f"{user_id}-{provider}-fixture"

        async def discover(**keys):
            return {"openai": [{"id": keys["openai_key"]}], "openrouter": []}

        redis = SimpleNamespace(get=AsyncMock(side_effect=cache_get), set=AsyncMock(side_effect=cache_set))
        with patch.object(models, "get_redis", AsyncMock(return_value=redis)), patch(
            "app.services.api_key_service.get_api_key", AsyncMock(side_effect=user_key)
        ), patch.object(models.model_discovery_service, "get_all_models", AsyncMock(side_effect=discover)) as fetch:
            a = await models.get_available_models(SimpleNamespace(id="user-a"), object())
            b = await models.get_available_models(SimpleNamespace(id="user-b"), object())
            again = await models.get_available_models(SimpleNamespace(id="user-a"), object())
            self.assertNotEqual(a, b)
            self.assertEqual(a, again)
            self.assertEqual(fetch.await_count, 2)
            self.assertEqual(set(cache), {"available_models:user-a", "available_models:user-b"})

    async def test_refresh_preserves_other_users_cache(self):
        redis = SimpleNamespace(delete=AsyncMock(), set=AsyncMock())
        with patch.object(models, "get_redis", AsyncMock(return_value=redis)), patch(
            "app.services.api_key_service.get_api_key", AsyncMock(return_value=None)
        ), patch.object(models.model_discovery_service, "get_all_models", AsyncMock(return_value={"openai": []})):
            result = await models.refresh_model_cache(SimpleNamespace(id="user-a"), object())
            self.assertTrue(result["success"])
            redis.delete.assert_awaited_once_with("available_models:user-a")
            redis.set.assert_awaited_once_with("available_models:user-a", json.dumps({"openai": []}), ex=3600)
