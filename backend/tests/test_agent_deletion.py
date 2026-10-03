"""Real PostgreSQL API regression: RUN_POSTGRES_TESTS=1 python -m unittest discover -s tests -v."""
import os
import unittest
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import psycopg
from psycopg import sql
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.api.routes.custom_agents import get_current_user
from app.models.user import User
from app.models.custom_agent import CustomAgent
from app.models.analytics import AgentAnalytics, ToolUsageLog


@unittest.skipUnless(os.getenv("RUN_POSTGRES_TESTS") == "1", "requires PostgreSQL")
class AgentDeletionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.database = "agent_delete_test_" + uuid4().hex
        self.admin = await psycopg.AsyncConnection.connect(
            settings.database_url.replace("postgresql+asyncpg://", "postgresql://"), autocommit=True
        )
        await self.admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database)))
        self.engine = create_async_engine(make_url(settings.database_url).set(database=self.database))
        async with self.engine.begin() as connection:
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await connection.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()
        await self.admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(self.database)))
        await self.admin.close()

    async def check_deletion(self, load_analytics):
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            owner = User(email="owner@example.com")
            stranger = User(email="stranger@example.com")
            session.add_all([owner, stranger])
            await session.flush()
            agents = [CustomAgent(user_id=owner.id, name=name, model_name="test", system_prompt="test")
                      for name in ["Delete me", "Keep me"]]
            session.add_all(agents)
            await session.flush()
            for agent in agents:
                session.add(AgentAnalytics(agent_id=agent.id, user_id=owner.id,
                                           date=datetime.now(timezone.utc), total_runs=1))
                session.add(ToolUsageLog(agent_id=agent.id, user_id=owner.id, tool_name="test"))
            await session.commit()
            deleted_id, retained_id = [agent.id for agent in agents]
            session.expunge_all()
            if load_analytics:
                agent = await session.get(CustomAgent, deleted_id)
                await session.refresh(agent, ["analytics"])

            async def db_override():
                yield session

            acting_user = stranger

            async def user_override():
                return acting_user

            previous = dict(app.dependency_overrides)
            app.dependency_overrides[get_db] = db_override
            app.dependency_overrides[get_current_user] = user_override
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    denied = await client.delete(f"/api/custom-agents/{deleted_id}")
                    self.assertEqual(denied.status_code, 400)
                    self.assertIsNotNone(await session.get(CustomAgent, deleted_id))
                    acting_user = owner
                    response = await client.delete(f"/api/custom-agents/{deleted_id}")
                    self.assertEqual(response.status_code, 204)
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous)

        async with AsyncSession(self.engine) as verification:
            self.assertIsNone(await verification.get(CustomAgent, deleted_id))
            self.assertIsNotNone(await verification.get(CustomAgent, retained_id))
            for model in [AgentAnalytics, ToolUsageLog]:
                rows = (await verification.execute(select(model.agent_id))).scalars().all()
                self.assertEqual(rows, [retained_id])

    async def test_delete_with_unloaded_analytics(self):
        await self.check_deletion(False)

    async def test_delete_with_loaded_analytics(self):
        await self.check_deletion(True)
