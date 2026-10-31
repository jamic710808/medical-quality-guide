from __future__ import annotations

from contextlib import asynccontextmanager
import json
from pathlib import Path
import re

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from . import delivery, evaluation, governance, knowledge_graph, release, remediation, retrieval, sources
from .access import PERMISSIONS, ROLE_NAMES, authenticate, get_case, issue_session, require, token_hash
from .clinical_context.context import case_context, import_case
from .common import Command, audit, check_version, command, digest, fail, public
from .config import PROJECT, settings
from .db import transaction
from .models import (
    Actor,
    Audit,
    Decision,
    Document,
    EvaluationBatch,
    Evidence,
    Export,
    Finding,
    Job,
    KnowledgeIndex,
    LoginSession,
    OntologyDraft,
    QualityRun,
    ReleaseRequest,
    Rule,
    SemanticRelease,
    Signature,
    Source,
    Task,
    now,
    uid,
)
from .ontology import get_release, import_rdf, resolve
from .quality import create_run


@asynccontextmanager
async def lifespan(app):
    # Schema and seed are explicit setup operations; startup never rewrites business state.
    yield


app = FastAPI(title="FF - 醫療病歷質控", version="0.1.0", lifespan=lifespan)
if not settings().session_secret:
    raise RuntimeError("缺少會話密鑰；先運行項目 setup，生產環境必須注入獨立密鑰。")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings().session_secret,
    session_cookie="mq_oidc_state",
    same_site="lax",
    https_only=settings().mode != "local",
)
oauth = OAuth()
if settings().oidc_issuer:
    oauth.register(
        name="hospital",
        client_id=settings().oidc_client_id,
        client_secret=settings().oidc_client_secret,
        server_metadata_url=settings().oidc_issuer.rstrip("/") + "/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile", "code_challenge_method": "S256"},
    )


@app.middleware("http")
async def response_security(request, call_next):
    request.state.request_id = uid()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Do not log SQL parameters, document text or model payloads on failure.
        import logging

        logging.getLogger("medical_quality").error(
            "request_failed request_id=%s error_type=%s", request.state.request_id, type(exc).__name__
        )
        response = JSONResponse(
            {
                "error": {
                    "code": "operation_failed",
                    "message": "操作未完整保存，請保留當前輸入並重試或核查。",
                    "request_id": request.state.request_id,
                }
            },
            status_code=500,
        )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(HTTPException)
async def api_error(request: Request, exc: HTTPException):
    actor = getattr(request.state, "actor", None)
    if actor and exc.status_code in {403, 404}:
        with transaction(actor) as db:
            audit(
                db,
                actor,
                "access.denied",
                "unavailable",
                outcome="denied",
                details={
                    "endpoint": request.url.path.split("/")[3]
                    if len(request.url.path.split("/")) > 3
                    else "api"
                },
            )
    elif exc.status_code == 401:
        from types import SimpleNamespace

        with transaction() as db:
            audit(
                db,
                SimpleNamespace(id="unverified", role="unverified"),
                "identity.denied",
                "unavailable",
                outcome="denied",
                details={"identity_verified": False, "request_id": request.state.request_id},
            )
    detail = (
        exc.detail if isinstance(exc.detail, dict) else {"code": "request_failed", "message": str(exc.detail)}
    )
    return JSONResponse({"error": detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        {
            "error": {
                "code": "validation_error",
                "message": "輸入不符合接口合同。",
                "fields": [list(e["loc"]) for e in exc.errors()],
            }
        },
        status_code=422,
    )


def actor_dep(request: Request):
    actor = authenticate(request)
    request.state.actor = actor
    return actor


def db_dep(request: Request, actor: Actor = Depends(actor_dep)):
    with transaction(actor) as db:
        db.info["request_id"] = request.state.request_id
        yield db


def session_response(db, actor, response=None):
    token, csrf = issue_session(db, actor)
    response = response or JSONResponse({"actor": public(actor), "identity_mode": settings().mode})
    response.set_cookie(
        "mq_session",
        token,
        httponly=True,
        samesite="strict",
        secure=settings().mode != "local",
        max_age=43200,
    )
    response.set_cookie(
        "mq_csrf", csrf, httponly=False, samesite="strict", secure=settings().mode != "local", max_age=43200
    )
    return response


@app.get("/api/health")
def health():
    with transaction() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "application": "medical-quality", "version": "0.1.0", "mode": settings().mode}


@app.get("/api/v1/auth/options")
def login_options():
    if settings().mode != "local":
        return {"mode": "oidc", "login_url": "/api/v1/auth/login"}
    with transaction() as db:
        actors = db.scalars(select(Actor).where(Actor.enabled.is_(True)).order_by(Actor.id)).all()
        return {
            "mode": "local",
            "description": "本地工程驗證身份，不代表醫院賬號或專業簽名",
            "actors": [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role,
                    "role_name": ROLE_NAMES[a.role],
                    "groups": a.groups,
                }
                for a in actors
            ],
        }


@app.post("/api/v1/auth/local")
def local_login(request: Request, payload: dict):
    if settings().mode != "local" or request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        fail("local_identity_disabled", "本地工程身份僅對本機開放。", 403)
    origin = request.headers.get("origin")
    if origin and origin != f"{request.url.scheme}://{request.url.netloc}":
        fail("origin_denied", "不接受跨站登錄。", 403)
    with transaction() as db:
        actor = db.get(Actor, payload.get("actor_id", ""))
        if not actor or not actor.enabled:
            fail("identity_unknown", "身份不可用。", 401)
        return session_response(db, actor)


@app.get("/api/v1/auth/login")
async def oidc_login(request: Request):
    if not settings().oidc_issuer:
        fail("oidc_not_configured", "醫院身份提供方尚未配置。", 503)
    return await oauth.hospital.authorize_redirect(request, str(request.url_for("oidc_callback")))


@app.get("/api/v1/auth/callback")
async def oidc_callback(request: Request):
    if not settings().oidc_issuer:
        fail("oidc_not_configured", "身份提供方尚未配置。", 503)
    try:
        token = await oauth.hospital.authorize_access_token(request)
        claims = token["userinfo"]
        if claims.get("iss") != settings().oidc_issuer:
            fail("issuer_invalid", "身份簽發方不匹配。", 401)
    except HTTPException:
        raise
    except Exception:
        fail("oidc_invalid", "身份回調校驗失敗。", 401)
    with transaction() as db:
        actor = db.scalar(select(Actor).where(Actor.oidc_subject == claims["sub"], Actor.enabled.is_(True)))
        if not actor:
            fail("identity_unmapped", "身份有效但尚未映射到本系統崗位。", 403)
        return session_response(db, actor, RedirectResponse("/"))


@app.get("/api/v1/session")
def current_session(actor: Actor = Depends(actor_dep)):
    return {
        "actor": public(actor),
        "permissions": sorted(PERMISSIONS[actor.role]),
        "identity_mode": settings().mode,
        "production_enabled": False,
    }


@app.get("/api/v1/events")
async def events(request: Request, actor: Actor = Depends(actor_dep)):
    import asyncio

    session_hash = token_hash(request.cookies.get("mq_session", ""))

    async def stream():
        while not await request.is_disconnected():
            with transaction() as db:
                current = db.get(Actor, actor.id)
                session = db.get(LoginSession, session_hash)
                valid = bool(
                    current
                    and current.enabled
                    and session
                    and session.expires_at > now()
                    and current.auth_version == session.auth_version
                    and (current.expires_at is None or current.expires_at > now())
                )
            if not valid:
                yield "event: authorization_revoked\ndata: {}\n\n"
                return
            yield 'event: heartbeat\ndata: {"status":"authorized"}\n\n'
            await asyncio.sleep(2)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})


@app.post("/api/v1/auth/logout")
def logout(
    request: Request, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    item = db.get(LoginSession, token_hash(request.cookies.get("mq_session", "")))
    if item:
        db.delete(item)
    audit(db, actor, "session.logout", actor.id)
    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie("mq_session")
    response.delete_cookie("mq_csrf")
    return response


@app.get("/api/v1/dashboard")
def dashboard(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    readable = "cases" in PERMISSIONS[actor.role]
    cases = db.scalars(select(Case)).all() if readable else []
    jobs = db.scalars(
        select(Job).where(Job.actor_id == actor.id).order_by(Job.created_at.desc()).limit(5)
    ).all()
    return {
        "case_count": len(cases),
        "pending": sum(c.status not in {"signed", "closed_false_positive", "checked"} for c in cases),
        "high_risk": sum(c.risk == "high" for c in cases),
        "signed": sum(c.status == "signed" for c in cases),
        "by_status": {s: sum(c.status == s for c in cases) for s in sorted({c.status for c in cases})},
        "jobs": [public(j, ("payload",)) for j in jobs],
        "scope": "當前授權病例",
        "semantic_status": "工程候選",
        "clinical_status": "未獲得生產准入",
    }


from .models import Case


@app.get("/api/v1/cases")
def list_cases(
    q="",
    state="",
    risk="",
    group="",
    page: int = 1,
    page_size: int = 10,
    sort="updated",
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    require(actor, "cases")
    page = max(1, page)
    page_size = max(1, min(50, page_size))
    stmt = select(Case)
    if q:
        stmt = stmt.where(or_(Case.display_name.ilike("%" + q + "%"), Case.encounter_id.ilike("%" + q + "%")))
    if state:
        stmt = stmt.where(Case.status == state)
    if risk:
        stmt = stmt.where(Case.risk == risk)
    if group:
        stmt = stmt.where(Case.group_id == group)
    count = db.scalar(select(func.count()).select_from(stmt.subquery()))
    ordering = {"updated": Case.created_at.desc(), "record": Case.encounter_id, "risk": Case.risk}.get(sort)
    if ordering is None:
        fail("sort_invalid", "排序字段不允許。", 422)
    items = db.scalars(stmt.order_by(ordering, Case.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [public(c) for c in items],
        "total": count,
        "page": page,
        "page_size": page_size,
        "scope": "authorized",
    }


@app.get("/api/v1/cases/{case_id}")
def detail(case_id: str, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    context = case_context(db, actor, case_id)
    runs = db.scalars(
        select(QualityRun).where(QualityRun.case_id == case_id).order_by(QualityRun.created_at.desc())
    ).all()
    tasks = db.scalars(
        select(Task)
        .where(Task.case_id == case_id, Task.state != "superseded")
        .order_by(Task.created_at.desc())
    ).all()
    findings = db.scalars(select(Finding).where(Finding.case_id == case_id)).all()
    visible_finding_ids = {t.finding_id for t in tasks}
    referenced_ids = {eid for f in findings if f.id in visible_finding_ids for eid in f.evidence_ids}
    current_ids = {e["id"] for e in context["evidence"]}
    if referenced_ids - current_ids:
        context["evidence"].extend(
            public(e)
            for e in db.scalars(select(Evidence).where(Evidence.id.in_(referenced_ids - current_ids)))
        )
    document_versions = [
        public(d, ("content", "fields"))
        for d in db.scalars(select(Document).where(Document.case_id == case_id))
    ]
    decisions = db.scalars(
        select(Decision).where(Decision.case_id == case_id).order_by(Decision.created_at)
    ).all()
    signatures = db.scalars(select(Signature).where(Signature.case_id == case_id)).all()
    actor_ids = (
        {context["case"]["owner_id"]} | {x.actor_id for x in decisions} | {x.actor_id for x in signatures}
    )
    for task in tasks:
        actor_ids.update([task.doctor_id, task.reviewer_id, task.expert_id])
    people = [
        {"id": a.id, "name": a.name, "role": a.role}
        for a in db.scalars(select(Actor).where(Actor.id.in_([i for i in actor_ids if i])))
    ]
    audit(db, actor, "case.read", case_id, case_id=case_id)
    return {
        **context,
        "runs": [public(x) for x in runs],
        "tasks": [public(x) for x in tasks],
        "findings": [public(x) for x in findings],
        "decisions": [public(x) for x in decisions],
        "signatures": [public(x) for x in signatures],
        "actors": people,
        "document_versions": document_versions,
    }


@app.get("/api/v1/evidence/{evidence_id}")
def evidence_detail(
    evidence_id: str, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    item = db.get(Evidence, evidence_id)
    if not item:
        fail("not_found", "證據不存在或當前不可讀。", 404)
    if item.data_role in {"reference_label", "validation", "heldout"}:
        fail("evaluator_only", "獨立參照資料不開放為建設證據。", 403)
    if item.case_id:
        get_case(db, actor, item.case_id)
    elif item.data_role == "business_evidence" and actor.role != "qc":
        fail("evidence_denied", "當前崗位不可讀取病例正文。", 403)
    else:
        require(actor, "knowledge")
    from .replay import verify

    replay = verify(db, item)
    document = db.get(Document, item.document_id) if item.document_id else None
    audit(db, actor, "evidence.read", item.id, case_id=item.case_id)
    return {"evidence": public(item), "document": public(document) if document else None, "replay": replay}


@app.get("/api/v1/evidence/{evidence_id}/page-image")
def evidence_page_image(
    evidence_id: str, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    from fastapi.responses import Response
    from .replay import pdf_page_image

    evidence_detail(evidence_id, actor, db)
    item = db.get(Evidence, evidence_id)
    raw = pdf_page_image(db, item)
    audit(
        db,
        actor,
        "evidence.page.read",
        item.id,
        case_id=item.case_id,
        details={"source_version": item.source_version, "page": item.envelope["locator"]["page"]},
    )
    return Response(raw, media_type="image/png", headers={"Cache-Control": "private, no-store"})


@app.post("/api/v1/cases/{case_id}/quality-runs")
def request_run(
    case_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    case = get_case(db, actor, case_id, lock=True, action="run")

    def perform():
        check_version(case, cmd.expected_version)
        run = create_run(db, actor, case.id, cmd.purpose, baseline=cmd.payload)
        job = Job(id=uid(), actor_id=actor.id, case_id=case.id, kind="quality", payload={"run_id": run.id})
        db.add(job)
        db.flush()
        return {"id": run.id, "job_id": job.id, "status": "queued"}

    return JSONResponse(command(db, actor, "quality.request", case.id, cmd, perform), status_code=202)


@app.post("/api/v1/evidence/{evidence_id}/case")
def evidence_case(
    evidence_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    require(actor, "review")
    return command(
        db,
        actor,
        "case.import",
        evidence_id,
        cmd,
        lambda: import_case(db, actor, evidence_id, cmd.payload.get("owner_id", "")),
    )


@app.post("/api/v1/tasks/{task_id}/{action}")
def task_action(
    task_id: str,
    action: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return remediation.act(db, actor, task_id, action, cmd)


@app.get("/api/v1/jobs")
def jobs(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    stmt = select(Job).where(Job.actor_id == actor.id).order_by(Job.created_at.desc()).limit(50)
    return {"items": [public(j, ("payload",)) for j in db.scalars(stmt)]}


@app.get("/api/v1/jobs/{job_id}")
def job_detail(
    job_id: str, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    job = db.get(Job, job_id)
    if not job or job.actor_id != actor.id:
        fail("not_found", "作業不可訪問。", 404)
    if job.case_id:
        get_case(db, actor, job.case_id)
    return public(job, ("payload",))


@app.post("/api/v1/jobs/{job_id}/retry")
def job_retry(
    job_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    job = db.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if not job or job.actor_id != actor.id:
        fail("not_found", "作業不可訪問。", 404)
    if job.case_id:
        get_case(db, actor, job.case_id)

    def perform():
        check_version(job, cmd.expected_version)
        if job.status != "failed":
            fail("job_not_failed", "只有已失敗作業可重試。")
        if job.attempt >= 3:
            fail("job_budget", "已達到自動嘗試上限，需要核查失敗原因並建立新運行。")
        job.status = "queued"
        job.version += 1
        job.error_code = None
        audit(db, actor, "job.retry", job.id, reason=cmd.reason, after=job.version)
        return public(job, ("payload",))

    return command(db, actor, "job.retry", job.id, cmd, perform)


@app.get("/api/v1/sources/catalogue")
def source_catalogue(actor: Actor = Depends(actor_dep)):
    require(actor, "sources")
    return {"items": [{k: v for k, v in x.items() if k != "path"} for x in sources.CATALOGUE]}


@app.get("/api/v1/sources")
def list_sources(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "sources")
    items = [
        public(s)
        for s in db.scalars(select(Source).order_by(Source.created_at.desc()))
        if not s.details.get("internal_document")
    ]
    from .evidence import coverage_summary

    return {"items": items, "coverage_summary": coverage_summary(items, len(items))}


@app.post("/api/v1/sources")
def register_source(
    payload: dict, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    return sources.register(db, actor, key=payload.get("catalogue_key"))


@app.post("/api/v1/sources/upload")
async def upload_source(
    request: Request,
    file: UploadFile = File(...),
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    require(actor, "source_register" if actor.role == "info" else "sources")
    name = Path(file.filename or "upload.bin").name
    ext = "".join(Path(name).suffixes)[-20:]
    if not re.fullmatch(r"[.a-zA-Z0-9]*", ext):
        fail("file_extension", "文件擴展名不允許。", 422)
    raw = await file.read(20 * 1024 * 1024 + 1)
    if len(raw) > 20 * 1024 * 1024:
        fail("upload_budget", "文件超過 20 MiB 上傳限制。", 413)
    folder = settings().artifacts / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (uid() + ext)
    path.write_bytes(raw)
    return sources.register(
        db,
        actor,
        upload={
            "name": name,
            "reference": "upload:" + path.name,
            "namespace": "local_upload",
            "role": "business_evidence",
            "kind": "unknown",
            "license": "上傳者尚需確認來源授權；僅限工程核查",
        },
    )


@app.get("/api/v1/sources/{source_id}/schema")
def source_schema(
    source_id: str, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    require(actor, "source_schema" if actor.role == "info" else "sources")
    source = db.get(Source, source_id)
    if not source:
        fail("not_found", "資料不可用。", 404)
    source, path = sources.source_for_read(db, actor, source.id, source.version)
    if source.format != "sqlite":
        fail("not_database", "此資料不是 SQLite 結構庫。", 422)
    result = sources.schema_catalog(path)
    audit(db, actor, "source.schema", source.id)
    return {"tables": result, "source_version": source.version}


@app.get("/api/v1/sources/{source_id}/evidence")
def source_evidence(
    source_id: str,
    page: int = 1,
    parse_run_id: str | None = None,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    source = db.get(Source, source_id)
    if not source:
        fail("not_found", "資料不可用。", 404)
    if source.data_role == "business_evidence" and actor.role != "qc":
        fail("body_denied", "當前崗位可以查看處理覆蓋，不能讀取病例正文。", 403)
    require(actor, "sources")
    stmt = select(Evidence).where(Evidence.source_id == source_id, Evidence.source_version == source.version)
    selected_run = parse_run_id or source.details.get("last_parse", {}).get("run_id")
    if selected_run:
        stmt = stmt.where(Evidence.envelope["provenance"]["run_id"].astext == selected_run)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(Evidence.created_at, Evidence.id).offset((max(1, page) - 1) * 20).limit(20)
    ).all()
    audit(db, actor, "source.evidence.read", source.id)
    return {
        "items": [public(e) for e in items],
        "total": total,
        "page": page,
        "page_size": 20,
        "parse_run_id": selected_run,
    }


@app.post("/api/v1/sources/{source_id}/structured-query")
def structured_query(
    source_id: str,
    payload: dict,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    from .clinical_context.query_catalog import query

    return query(db, actor, source_id, payload.get("operation", ""), payload.get("parameters", {}))


@app.post("/api/v1/source-versions/{source_id}/parse-runs")
def parse_request(
    source_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    source, path = sources.source_for_read(db, actor, source_id, cmd.expected_version)

    def perform():
        job = Job(
            id=uid(),
            actor_id=actor.id,
            kind="parse",
            payload={"source_id": source.id, "version": cmd.expected_version, "scope": cmd.payload},
        )
        db.add(job)
        db.flush()
        audit(db, actor, "source.parse.request", source.id, reason=cmd.reason, details={"job_id": job.id})
        return {"id": job.id, "status": "queued", "source_id": source.id}

    return JSONResponse(command(db, actor, "source.parse", source.id, cmd, perform), status_code=202)


@app.get("/api/v1/rules")
def rules(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "knowledge")
    return {
        "items": [public(r) for r in db.scalars(select(Rule).order_by(Rule.rule_key, Rule.version.desc()))]
    }


@app.post("/api/v1/rules/{rule_id}/status")
def rule_status(
    rule_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    require(actor, "knowledge_edit")
    rule = db.scalar(select(Rule).where(Rule.id == rule_id).with_for_update())
    if not rule:
        fail("rule_missing", "規則不存在。", 404)

    def perform():
        if rule.policy_version != cmd.expected_version:
            fail("version_conflict", "規則資格已變化，請刷新核對。")
        new = cmd.payload.get("status")
        if new not in {"candidate", "retired"}:
            fail(
                "professional_review_required",
                "生產批准須目標環境的專業審核，當前入口只管理候選或停用。",
                422,
            )
        rule.status = new
        rule.policy_version += 1
        audit(db, actor, "rule.status", rule.id, reason=cmd.reason, after=rule.policy_version)
        return public(rule)

    return command(db, actor, "rule.status", rule.id, cmd, perform)


@app.post("/api/v1/rules/{rule_id}/versions")
def rule_version(
    rule_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return governance.new_rule_version(db, actor, rule_id, cmd)


@app.post("/api/v1/rules/{rule_id}/review")
def rule_review(
    rule_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return governance.review_rule(db, actor, rule_id, cmd)


@app.get("/api/v1/knowledge/search")
def search_knowledge(
    q: str,
    release_id="semantic-v1",
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return retrieval.retrieve(db, actor, q, release_id)


@app.get("/api/v1/knowledge/indices")
def knowledge_indices(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "knowledge")
    return {
        "items": [
            public(i) for i in db.scalars(select(KnowledgeIndex).order_by(KnowledgeIndex.created_at.desc()))
        ]
    }


@app.post("/api/v1/knowledge/indices")
def knowledge_index_request(
    cmd: Command, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    require(actor, "knowledge_edit")
    release_id = cmd.payload.get("release_id", "semantic-v1")
    get_release(db, release_id)

    def perform():
        job = Job(id=uid(), actor_id=actor.id, kind="index", payload={"release_id": release_id})
        db.add(job)
        db.flush()
        audit(db, actor, "knowledge.index.request", job.id, reason=cmd.reason)
        return {"id": job.id, "status": "queued"}

    return JSONResponse(command(db, actor, "knowledge.index", release_id, cmd, perform), status_code=202)


@app.get("/api/v1/semantic/releases")
def releases(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "knowledge")
    return {"items": [public(r, ("ontology",)) for r in db.scalars(select(SemanticRelease))]}


@app.get("/api/v1/semantic/releases/{release_id}/package")
def semantic_package(
    release_id: str, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    import io, zipfile
    from fastapi.responses import Response

    require(actor, "export_graph")
    record = get_release(db, release_id)
    root = settings().artifacts / "ontology"
    folder = (root / record.id).resolve()
    if not folder.is_relative_to(root.resolve()):
        fail("package_scope", "本體資源不可訪問。", 404)
    files = {
        "core.ttl": "core",
        "shapes.ttl": "shapes",
        "mappings.sssom.tsv": "mappings",
        "bindings.json": "bindings",
    }
    contents = {}
    for filename, key in files.items():
        path = folder / filename
        if not path.is_file() or digest(path.read_bytes()) != record.manifest[key]:
            fail("package_integrity", "固定本體包缺失或摘要不一致。")
        contents[filename] = path.read_bytes()
    for filename in ["imports.json", "classified.owl", "profile.txt", "validation.json"]:
        path = folder / filename
        if path.is_file():
            contents[filename] = path.read_bytes()
    contents["manifest.json"] = json.dumps(
        public(record, ("ontology",)), ensure_ascii=False, indent=2
    ).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, body in contents.items():
            archive.writestr(name, body)
    audit(
        db,
        actor,
        "ontology.package.export",
        record.id,
        details={"semantic_digest": record.digest, "purpose": record.purpose},
    )
    return Response(
        buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="ontology-{record.id}.zip"'},
    )


@app.post("/api/v1/semantic/resolve")
def semantic_resolve(
    payload: dict, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    require(actor, "knowledge")
    return resolve(db, payload.get("release_id", "semantic-v1"), payload.get("mentions", [])[:20])


@app.get("/api/v1/knowledge-graphs/views")
def graph_view(
    view_kind="ontology",
    scope_ref: str | None = None,
    release_id="semantic-v1",
    run_id: str | None = None,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return knowledge_graph.view(db, actor, view_kind, scope_ref, release_id, run_id)


@app.post("/api/v1/knowledge-graphs/import")
def graph_import(payload: dict, actor: Actor = Depends(actor_dep)):
    require(actor, "draft")
    return import_rdf(payload.get("content", ""), payload.get("format", "xml"))


@app.post("/api/v1/knowledge-graphs/drafts")
def graph_draft(
    payload: dict, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    return knowledge_graph.save_draft(db, actor, payload)


@app.get("/api/v1/knowledge-graphs/drafts")
def graph_drafts(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "draft")
    stmt = (
        select(OntologyDraft)
        .where(
            or_(OntologyDraft.actor_id == actor.id, OntologyDraft.review["reviewer_id"].astext == actor.id)
        )
        .order_by(OntologyDraft.created_at.desc())
    )
    return {"items": [public(d) for d in db.scalars(stmt)]}


@app.patch("/api/v1/knowledge-graphs/drafts/{draft_id}")
def graph_update(
    draft_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return command(
        db,
        actor,
        "ontology.draft.save",
        draft_id,
        cmd,
        lambda: knowledge_graph.save_draft(db, actor, cmd.payload, draft_id, cmd),
    )


@app.post("/api/v1/knowledge-graphs/drafts/{draft_id}/submit")
def graph_submit(
    draft_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return knowledge_graph.submit_draft(db, actor, draft_id, cmd)


@app.post("/api/v1/knowledge-graphs/drafts/{draft_id}/review")
def graph_review(
    draft_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return governance.review_draft(db, actor, draft_id, cmd)


@app.post("/api/v1/knowledge-graphs/export-authorizations")
def graph_export(
    payload: dict, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    return knowledge_graph.authorize_export(db, actor, payload)


@app.get("/api/v1/evaluation-batches")
def batches(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "evaluation_report" if actor.role == "manager" else "evaluation")
    items = db.scalars(select(EvaluationBatch).order_by(EvaluationBatch.created_at.desc())).all()
    if actor.role == "expert":
        items = [b for b in items if actor.id in b.assignments["raters"] + [b.assignments["arbitrator"]]]
    return {"items": [public(b, ("samples",)) for b in items]}


@app.post("/api/v1/evaluation-batches")
def new_batch(
    payload: dict, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    return evaluation.create_batch(db, actor, payload)


@app.get("/api/v1/evaluation-batches/{batch_id}/report")
def eval_report(
    batch_id: str, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    return evaluation.report(db, actor, batch_id)


@app.post("/api/v1/evaluation-batches/{batch_id}/judgments")
def eval_judge(
    batch_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return evaluation.judge(db, actor, batch_id, cmd)


@app.post("/api/v1/evaluation-batches/{batch_id}/arbitrations")
def eval_arbitrate(
    batch_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return evaluation.arbitrate(db, actor, batch_id, cmd)


@app.post("/api/v1/evaluation-batches/{batch_id}/protocol")
def eval_protocol(
    batch_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return evaluation.freeze_protocol(db, actor, batch_id, cmd)


@app.get("/api/v1/evaluation-batches/{batch_id}/samples/{sample_id}")
def eval_sample(
    batch_id: str,
    sample_id: str,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return evaluation.sample_detail(db, actor, batch_id, sample_id)


@app.get("/api/v1/evaluation-batches/{batch_id}/compare/{other_id}")
def eval_compare(
    batch_id: str,
    other_id: str,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return evaluation.compare_reports(
        evaluation.report(db, actor, batch_id), evaluation.report(db, actor, other_id)
    )


@app.get("/api/v1/release-requests")
def release_list(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    if actor.role not in {"manager", "qc", "doctor", "info"}:
        fail("release_denied", "當前崗位不可查看準入。", 403)
    return {
        "items": [
            public(r) for r in db.scalars(select(ReleaseRequest).order_by(ReleaseRequest.created_at.desc()))
        ]
    }


@app.post("/api/v1/release-requests")
def release_create(
    payload: dict, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    return release.create_request(db, actor, payload)


@app.post("/api/v1/release-requests/{request_id}/decisions")
def release_decide(
    request_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return release.decide(db, actor, request_id, cmd)


@app.post("/api/v1/release-requests/{request_id}/acceptances")
def release_accept(
    request_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return release.accept_responsibility(db, actor, request_id, cmd)


@app.post("/api/v1/release-requests/{request_id}/stop")
def release_stop(
    request_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    return release.stop_release(db, actor, request_id, cmd)


@app.get("/api/v1/exports")
def exports(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "export_assets")
    return {
        "items": [
            public(x)
            for x in db.scalars(
                select(Export).where(Export.actor_id == actor.id).order_by(Export.created_at.desc())
            )
        ]
    }


@app.post("/api/v1/exports")
def export_create(
    payload: dict, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    return delivery.build_export(db, actor, payload.get("release_request_id", ""))


@app.get("/api/v1/exports/{export_id}/download")
def export_download(
    export_id: str, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")
):
    require(actor, "export_assets")
    item = db.get(Export, export_id)
    if not item or item.actor_id != actor.id:
        fail("not_found", "交付包不可訪問。", 404)
    path = (settings().artifacts / item.artifact_ref).resolve()
    if (
        not path.is_relative_to(settings().artifacts.resolve())
        or not path.is_file()
        or sources.hash_file(path) != item.digest
    ):
        fail("export_integrity", "交付文件缺失或摘要不一致。")
    audit(db, actor, "asset.download", item.id)
    return FileResponse(path, filename="醫療質控交付-" + item.id[:8] + ".zip")


@app.get("/api/v1/audit-events")
def audits(page: int = 1, actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "audit")
    stmt = select(Audit)
    if actor.role == "qc":
        stmt = stmt.where(or_(Audit.actor_id == actor.id, Audit.case_id.in_(select(Case.id))))
    stmt = stmt.order_by(Audit.created_at.desc(), Audit.id).offset((max(page, 1) - 1) * 30).limit(30)
    items = []
    for event in db.scalars(stmt):
        item = public(event)
        if event.case_id and actor.role in {"info", "manager"}:
            item["reason"] = "專業意見僅限當前病例獲權人員查看"
            item["details"] = {
                k: v
                for k, v in item["details"].items()
                if k in {"request_id", "decision_id", "run_id", "status", "before_state", "after_state"}
            }
        items.append(item)
    return {"items": items, "page": page}


@app.get("/api/v1/access/actors")
def actors(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    if actor.role not in {"info", "qc", "manager", "expert"}:
        fail("actor_directory_denied", "當前崗位不能讀取人員目錄。", 403)
    return {
        "items": [public(a, ("oidc_subject",)) for a in db.scalars(select(Actor).order_by(Actor.id))],
        "permissions": {role: sorted(actions) for role, actions in PERMISSIONS.items()},
    }


@app.get("/api/v1/operations/status")
def operation_status(actor: Actor = Depends(actor_dep), db: Session = Depends(db_dep, scope="function")):
    require(actor, "operations")
    from .quality import model_manifest

    db_role = db.execute(text("SELECT current_user")).scalar()
    audit(db, actor, "operations.status", "runtime", details={"clinical_content": False})
    return {
        "application_version": "0.1.0",
        "mode": settings().mode,
        "database": "PostgreSQL 17 / pgvector",
        "database_role": db_role,
        "api": "available",
        "identity_provider_configured": bool(settings().oidc_issuer),
        "model": model_manifest(),
        "ocr_resources_prepared": (settings().artifacts / "models/ocr-manifest.json").exists(),
        "ontology": "OWL 2 EL / ELK / SHACL",
        "original_data_access": "read_only",
        "clinical_qualification": "not_evaluated",
        "diagnostic_scope": "服務與資源元數據；不包含病例正文、憑據或後臺任意執行入口",
    }


@app.post("/api/v1/access/actors/{actor_id}/revoke")
def revoke(
    actor_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    require(actor, "manage_access")
    target = db.scalar(select(Actor).where(Actor.id == actor_id).with_for_update())
    if not target or target.id == actor.id:
        fail("revocation_target", "請選擇其他有效主體。", 422)

    def perform():
        check_version(target, cmd.expected_version)
        target.enabled = False
        target.auth_version += 1
        target.version += 1
        audit(db, actor, "access.revoke", target.id, reason=cmd.reason, after=target.version)
        return public(target, ("oidc_subject",))

    return command(db, actor, "access.revoke", target.id, cmd, perform)


@app.post("/api/v1/access/actors/{actor_id}/restore")
def restore_access(
    actor_id: str,
    cmd: Command,
    actor: Actor = Depends(actor_dep),
    db: Session = Depends(db_dep, scope="function"),
):
    from datetime import datetime

    require(actor, "manage_access")
    target = db.scalar(select(Actor).where(Actor.id == actor_id).with_for_update())
    if not target or target.id == actor.id:
        fail("authorization_target", "請選擇其他已登記主體。", 422)

    def perform():
        check_version(target, cmd.expected_version)
        try:
            expiry = datetime.fromisoformat(cmd.payload["expires_at"])
        except (KeyError, TypeError, ValueError):
            fail("authorization_expiry", "請提供明確的授權截止時間。", 422)
        if expiry.tzinfo is None or expiry <= now():
            fail("authorization_expiry", "授權截止時間必須包含時區並晚於當前時間。", 422)
        target.enabled = True
        target.expires_at = expiry
        target.auth_version += 1
        target.version += 1
        audit(
            db,
            actor,
            "access.restore",
            target.id,
            reason=cmd.reason,
            after=target.version,
            details={"expires_at": expiry.isoformat(), "scope_changed": False},
        )
        return public(target, ("oidc_subject",))

    return command(db, actor, "access.restore", target.id, cmd, perform)


DIST = PROJECT / "frontend/dist"
if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
app.mount("/brand", StaticFiles(directory=PROJECT / "frontend/public/brand"), name="brand")
app.mount("/licenses", StaticFiles(directory=PROJECT / "frontend/public/licenses"), name="licenses")


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    if path.startswith("api/"):
        fail("not_found", "接口不存在。", 404)
    entry = DIST / "index.html"
    if not entry.exists():
        return JSONResponse({"message": "正式前端尚未構建，請運行 npm run build。"}, status_code=503)
    return FileResponse(entry)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8180, access_log=False)
