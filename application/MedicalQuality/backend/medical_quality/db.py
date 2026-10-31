from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from .config import settings
from .models import Actor


@lru_cache(maxsize=1)
def engine():
    url = settings().database_url
    if not url:
        raise RuntimeError("請先運行 python3 scripts/manage.py setup 建立項目數據庫")
    return create_engine(url, pool_pre_ping=True, pool_size=8, max_overflow=8)


def set_actor(db: Session, actor: Actor | None) -> None:
    context = {
        "mq.actor": actor.id if actor else "",
        "mq.role": actor.role if actor else "",
        "mq.groups": ",".join(actor.groups) if actor and actor.role == "qc" else "",
        "mq.cases": ",".join(actor.case_ids) if actor else "",
    }
    for key, value in context.items():
        db.execute(text("SELECT set_config(:key, :value, true)"), {"key": key, "value": value})


@contextmanager
def transaction(actor: Actor | None = None):
    with Session(engine(), expire_on_commit=False) as db:
        with db.begin():
            set_actor(db, actor)
            yield db
