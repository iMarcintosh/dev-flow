"""Optional real-PostgreSQL regression test; never calls an AI provider.

Run with RUN_POSTGRES_TESTS=1 python -m unittest discover -s tests -v.
The configured database user must be able to create a disposable database.
"""
import asyncio
import os
import unittest
from uuid import uuid4
from unittest.mock import patch

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from langgraph.checkpoint.base import empty_checkpoint
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings
from app.agent.custom_agent_runner import _get_postgres_conn_string
from app.main import startup_event


@unittest.skipUnless(os.getenv("RUN_POSTGRES_TESTS") == "1", "requires PostgreSQL")
class ChatCheckpointerTests(unittest.IsolatedAsyncioTestCase):
    async def test_startup_prepares_memory_before_request_transaction(self):
        database = "chat_test_" + uuid4().hex
        admin = await psycopg.AsyncConnection.connect(
            _get_postgres_conn_string(), autocommit=True
        )
        await admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        dsn = make_conninfo(_get_postgres_conn_string(), dbname=database)
        try:
            with patch.object(settings, "database_url", dsn):
                await asyncio.wait_for(startup_event(), timeout=20)
                # A request reads database state and holds its transaction while
                # awaiting the stream. Concurrent index migrations here can wait
                # indefinitely for that very transaction to finish.
                async with await psycopg.AsyncConnection.connect(dsn) as request:
                    await request.execute("SELECT * FROM checkpoints LIMIT 1")
                    async with AsyncPostgresSaver.from_conn_string(dsn) as saver:
                        config = {"configurable": {"thread_id": "regression", "checkpoint_ns": ""}}
                        saved = await asyncio.wait_for(
                            saver.aput(config, empty_checkpoint(), {}, {}), timeout=5
                        )
                        checkpoint = await asyncio.wait_for(saver.aget_tuple(saved), timeout=5)
                        self.assertIsNotNone(checkpoint)
                        self.assertEqual(checkpoint.config["configurable"]["thread_id"], "regression")
        finally:
            await admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
            await admin.close()
