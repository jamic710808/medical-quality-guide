from __future__ import annotations
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from langgraph.checkpoint.postgres import PostgresSaver

from medical_quality.config import settings
from medical_quality.db import engine


@pytest.fixture(scope="session", autouse=True)
def database_seed():
    admin = os.environ.get("MQ_TEST_ADMIN_URL", "")
    if not admin.endswith("/medical_quality_test"):
        raise RuntimeError("必須通過 scripts/test_backend.py 在獨立測試庫執行。")
    privileged = create_engine(admin.replace("postgresql://", "postgresql+psycopg://"))
    # This named database contains only reproducible synthetic engineering test data.
    with privileged.begin() as db:
        tables = (
            db.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename != 'alembic_version'"
                )
            )
            .scalars()
            .all()
        )
        if tables:
            db.execute(
                text("TRUNCATE " + ",".join('"' + t + '"' for t in tables) + " RESTART IDENTITY CASCADE")
            )
    original = os.environ["MQ_DATABASE_URL"]
    os.environ["MQ_DATABASE_URL"] = admin.replace("postgresql://", "postgresql+psycopg://")
    engine.cache_clear()
    from medical_quality.seed import seed

    seed()
    engine().dispose()
    engine.cache_clear()
    os.environ["MQ_DATABASE_URL"] = original
    with PostgresSaver.from_conn_string(settings().checkpoint_url) as saver:
        saver.setup()
    yield
    engine().dispose()
    privileged.dispose()


@pytest.fixture
def client():
    from medical_quality.app import app

    with TestClient(app) as value:
        yield value


def login(client, actor="qc1"):
    response = client.post("/api/v1/auth/local", json={"actor_id": actor})
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": client.cookies.get("mq_csrf")}


def cmd(version=1, payload=None, reason="工程驗證：固定範圍與責任行為", key=None):
    return {
        "expected_version": version,
        "idempotency_key": key or str(uuid.uuid4()),
        "reason": reason,
        "payload": payload or {},
        "purpose": "engineering",
    }
