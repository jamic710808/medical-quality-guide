#!/usr/bin/env python3
"""建立獨立可重建測試數據庫，實際業務試用庫不受測試清理影響。"""

from pathlib import Path
import json
import os
import subprocess
import sys

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / ".runtime/config.json").read_text())
admin = config["migration_url"].replace("postgresql+psycopg://", "postgresql://")
database = "medical_quality_test"
with psycopg.connect(admin, autocommit=True) as conn:
    if not conn.execute(
        "SELECT 1 FROM pg_database WHERE datname=%s", (database,)
    ).fetchone():
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
test_admin = admin.rsplit("/", 1)[0] + "/" + database
with psycopg.connect(test_admin, autocommit=True) as conn:
    conn.execute("CREATE SCHEMA IF NOT EXISTS checkpoints AUTHORIZATION mq_checkpoint")
environment = {
    **os.environ,
    "MQ_DATABASE_URL": config["database_url"].rsplit("/", 1)[0] + "/" + database,
    "MQ_CHECKPOINT_URL": config["checkpoint_url"].rsplit("/", 1)[0] + "/" + database,
    "MQ_TEST_ADMIN_URL": test_admin,
    "MQ_MIGRATION_URL": test_admin.replace("postgresql://", "postgresql+psycopg://"),
    "MQ_MODE": "local",
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
}
subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=ROOT / "backend",
    env=environment,
    check=True,
)
args = sys.argv[1:] or ["-q"]
raise SystemExit(
    subprocess.run(
        [sys.executable, "-m", "pytest", *args], cwd=ROOT / "backend", env=environment
    ).returncode
)
