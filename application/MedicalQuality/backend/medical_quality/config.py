from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent


@dataclass(frozen=True)
class Settings:
    database_url: str
    checkpoint_url: str
    session_secret: str
    mode: str
    artifacts: Path
    data_root: Path
    model_url: str
    model_key: str
    oidc_issuer: str
    oidc_client_id: str
    oidc_client_secret: str


def settings() -> Settings:
    path = PROJECT / ".runtime/config.json"
    local = json.loads(path.read_text()) if path.exists() else {}
    return Settings(
        database_url=os.getenv("MQ_DATABASE_URL", local.get("database_url", "")),
        checkpoint_url=os.getenv("MQ_CHECKPOINT_URL", local.get("checkpoint_url", "")),
        session_secret=os.getenv("MQ_SESSION_SECRET", local.get("session_secret", "")),
        mode=os.getenv("MQ_MODE", local.get("mode", "production")),
        artifacts=PROJECT / "artifacts",
        data_root=WORKSPACE / "Data/醫療病歷質控",
        model_url=os.getenv("MQ_MODEL_URL", "http://127.0.0.1:8191"),
        model_key=os.getenv("MQ_MODEL_KEY", local.get("model_key", "")),
        oidc_issuer=os.getenv("MQ_OIDC_ISSUER", ""),
        oidc_client_id=os.getenv("MQ_OIDC_CLIENT_ID", ""),
        oidc_client_secret=os.getenv("MQ_OIDC_CLIENT_SECRET", ""),
    )
