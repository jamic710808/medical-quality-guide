from __future__ import annotations

from datetime import timedelta
import os
import signal
import socket
import threading
import time

from fastapi import HTTPException
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy import or_, select, update

from .access import refresh_actor
from .common import fail
from .config import settings
from .db import transaction
from .evidence import ingest_source
from .models import Job, QualityRun, now
from .quality import compute_run, execute_run
from .remediation import resume_human, wait_for_human
from .retrieval import build_index

OWNER = f"{socket.gethostname()}:{os.getpid()}"


def claim():
    with transaction() as db:
        job = db.scalar(
            select(Job)
            .where(or_(Job.status == "queued", (Job.status == "running") & (Job.lease_until < now())))
            .order_by(Job.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if not job:
            return None
        if job.attempt >= 3:
            job.status = "failed"
            job.error_code = "attempt_budget_exhausted"
            return None
        job.status = "running"
        job.attempt += 1
        job.fencing_token += 1
        job.lease_owner = OWNER
        job.heartbeat_at = now()
        job.lease_until = now() + timedelta(seconds=45)
        return {
            "id": job.id,
            "token": job.fencing_token,
            "actor_id": job.actor_id,
            "attempt": job.attempt,
            "kind": job.kind,
            "payload": job.payload,
        }


def heartbeat(claimed, stop):
    while not stop.wait(10):
        try:
            with transaction() as db:
                db.execute(
                    update(Job)
                    .where(
                        Job.id == claimed["id"],
                        Job.fencing_token == claimed["token"],
                        Job.status == "running",
                    )
                    .values(heartbeat_at=now(), lease_until=now() + timedelta(seconds=45))
                )
        except Exception:
            return


def process(claimed):
    stop = threading.Event()
    thread = threading.Thread(target=heartbeat, args=(claimed, stop), daemon=True)
    thread.start()
    try:
        computed = (
            compute_run(claimed["actor_id"], claimed["payload"]["run_id"], claimed["attempt"])
            if claimed["kind"] == "quality"
            else None
        )
        index_result = (
            build_index(
                claimed["actor_id"], claimed["payload"].get("release_id", "semantic-v1"), lease=claimed
            )
            if claimed["kind"] == "index"
            else None
        )
        with transaction() as db:
            actor = refresh_actor(db, claimed["actor_id"])
            if claimed["kind"] == "parse":
                payload = claimed["payload"]
                result = ingest_source(
                    db,
                    actor,
                    payload["source_id"],
                    payload["version"],
                    claimed["id"],
                    payload.get("scope", {}),
                )
            elif claimed["kind"] == "quality":
                run = db.get(QualityRun, claimed["payload"]["run_id"])
                if not run:
                    fail("run_missing", "運行已不可用。", 404)
                if run.status in {"needs_review", "partial"}:
                    result = {"id": run.id, "status": run.status, "reconciled": True}
                else:
                    run.status = "running"
                    result = execute_run(db, actor, run, claimed["attempt"], computed)
            elif claimed["kind"] == "human_resume":
                result = resume_human(db, actor, **claimed["payload"])
            elif claimed["kind"] == "human_wait":
                result = wait_for_human(db, actor, **claimed["payload"])
            elif claimed["kind"] == "index":
                result = index_result
            else:
                fail("unknown_job", "作業類型不受支持。", 422)
            refresh_actor(db, actor.id)
            job = db.scalar(select(Job).where(Job.id == claimed["id"]).with_for_update())
            if job.fencing_token != claimed["token"] or job.lease_owner != OWNER or job.status != "running":
                fail("stale_worker", "舊嘗試不可提交。")
            job.result = result
            job.status = "completed"
            job.lease_until = None
            job.heartbeat_at = now()
    except Exception as exc:
        code = (
            exc.detail.get("code", "job_failed")
            if isinstance(exc, HTTPException) and isinstance(exc.detail, dict)
            else type(exc).__name__
        )
        with transaction() as db:
            job = db.scalar(select(Job).where(Job.id == claimed["id"]).with_for_update())
            if job and job.fencing_token == claimed["token"] and job.status == "running":
                job.status = "failed"
                job.error_code = code
                job.lease_until = None
        print(f"job={claimed['id']} outcome=failed code={code}", flush=True)
    finally:
        stop.set()
        thread.join(timeout=1)


def main():
    with PostgresSaver.from_conn_string(settings().checkpoint_url) as saver:
        saver.setup()
    print("worker ready", flush=True)
    running = True

    def shutdown(*args):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    while running:
        item = claim()
        if item:
            process(item)
        else:
            time.sleep(0.5)


if __name__ == "__main__":
    main()
