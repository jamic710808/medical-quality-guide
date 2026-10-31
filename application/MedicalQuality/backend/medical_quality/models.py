from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now() -> datetime:
    return datetime.now(timezone.utc)


def uid() -> str:
    return uuid4().hex


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String(96), primary_key=True, default=uid)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class Actor(Record, Base):
    __tablename__ = "actors"
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30))
    groups: Mapped[list] = mapped_column(JSONB, default=list)
    case_ids: Mapped[list] = mapped_column(JSONB, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auth_version: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    oidc_subject: Mapped[str | None] = mapped_column(String(255), unique=True)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    auth_version: Mapped[int] = mapped_column(Integer)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Audit(Record, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str] = mapped_column(String(96))
    role: Mapped[str] = mapped_column(String(30))
    action: Mapped[str] = mapped_column(String(96), index=True)
    resource_id: Mapped[str] = mapped_column(String(96), index=True)
    case_id: Mapped[str | None] = mapped_column(String(96), index=True)
    purpose: Mapped[str] = mapped_column(String(40))
    outcome: Mapped[str] = mapped_column(String(40))
    before_version: Mapped[int | None] = mapped_column(Integer)
    after_version: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text, default="")
    operation_id: Mapped[str | None] = mapped_column(String(96), index=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)


class Operation(Record, Base):
    __tablename__ = "operations"
    __table_args__ = (UniqueConstraint("actor_id", "action", "target_id", "operation_key"),)
    actor_id: Mapped[str] = mapped_column(String(96))
    action: Mapped[str] = mapped_column(String(96))
    target_id: Mapped[str] = mapped_column(String(96))
    operation_key: Mapped[str] = mapped_column(String(100))
    request_digest: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSONB)


class Outbox(Record, Base):
    __tablename__ = "outbox"
    kind: Mapped[str] = mapped_column(String(96))
    aggregate_id: Mapped[str] = mapped_column(String(96))
    payload: Mapped[dict] = mapped_column(JSONB)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Source(Record, Base):
    __tablename__ = "sources"
    name: Mapped[str] = mapped_column(String(255))
    namespace: Mapped[str] = mapped_column(String(96))
    reference: Mapped[str] = mapped_column(Text)
    format: Mapped[str] = mapped_column(String(40))
    data_role: Mapped[str] = mapped_column(String(40))
    data_kind: Mapped[str] = mapped_column(String(40))
    purpose: Mapped[str] = mapped_column(String(40))
    license: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="registered")
    digest: Mapped[str] = mapped_column(String(64))
    scope: Mapped[dict] = mapped_column(JSONB, default=dict)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)


class SourceSnapshot(Record, Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (UniqueConstraint("source_id", "version"),)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"))
    digest: Mapped[str] = mapped_column(String(64))
    reference: Mapped[str] = mapped_column(Text)
    manifest: Mapped[dict] = mapped_column(JSONB)


class Case(Record, Base):
    __tablename__ = "cases"
    __table_args__ = (UniqueConstraint("namespace", "encounter_id"),)
    namespace: Mapped[str] = mapped_column(String(96))
    encounter_id: Mapped[str] = mapped_column(String(96))
    patient_key: Mapped[str] = mapped_column(String(96))
    display_name: Mapped[str] = mapped_column(String(120))
    group_id: Mapped[str] = mapped_column(String(50))
    owner_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    department: Mapped[str] = mapped_column(String(80), default="內科一病區")
    disease_scope: Mapped[str] = mapped_column(String(80), default="成人肺炎文書質控")
    data_kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="pending")
    risk: Mapped[str] = mapped_column(String(20), default="unknown")
    details: Mapped[dict] = mapped_column(JSONB, default=dict)


class Document(Record, Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("case_id", "document_key", "version"),)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    document_key: Mapped[str] = mapped_column(String(96))
    title: Mapped[str] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    digest: Mapped[str] = mapped_column(String(64))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"))
    author_id: Mapped[str] = mapped_column(String(96))
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"))
    fields: Mapped[dict] = mapped_column(JSONB, default=dict)


class Evidence(Record, Base):
    __tablename__ = "evidence_items"
    case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    source_version: Mapped[int] = mapped_column(Integer)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"))
    data_role: Mapped[str] = mapped_column(String(40))
    envelope: Mapped[dict] = mapped_column(JSONB)


class SemanticRelease(Record, Base):
    __tablename__ = "semantic_releases"
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40))
    purpose: Mapped[str] = mapped_column(String(40))
    digest: Mapped[str] = mapped_column(String(64))
    ontology: Mapped[dict] = mapped_column(JSONB)
    manifest: Mapped[dict] = mapped_column(JSONB)
    validation: Mapped[dict] = mapped_column(JSONB)


class OntologyDraft(Record, Base):
    __tablename__ = "ontology_drafts"
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    base_release_id: Mapped[str] = mapped_column(ForeignKey("semantic_releases.id"))
    status: Mapped[str] = mapped_column(String(40), default="draft")
    ontology: Mapped[dict] = mapped_column(JSONB)
    metadata_map: Mapped[dict] = mapped_column(JSONB, default=dict)
    loss_report: Mapped[list] = mapped_column(JSONB, default=list)
    review: Mapped[dict] = mapped_column(JSONB, default=dict)


class Rule(Record, Base):
    __tablename__ = "rules"
    __table_args__ = (UniqueConstraint("rule_key", "version"),)
    rule_key: Mapped[str] = mapped_column(String(80), index=True)
    policy_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(40), default="candidate")
    purpose: Mapped[str] = mapped_column(String(40), default="engineering")
    semantic_release_id: Mapped[str] = mapped_column(ForeignKey("semantic_releases.id"))
    content: Mapped[str] = mapped_column(Text)
    specification: Mapped[dict] = mapped_column(JSONB)
    provenance: Mapped[dict] = mapped_column(JSONB)


class KnowledgeChunk(Record, Base):
    __tablename__ = "knowledge_chunks"
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.id"))
    evidence_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_items.id"))
    text: Mapped[str] = mapped_column(Text)
    parent_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(Vector(1024))
    index_version: Mapped[str] = mapped_column(String(96))
    embedding_model: Mapped[str | None] = mapped_column(String(160))


class KnowledgeIndex(Record, Base):
    __tablename__ = "knowledge_indices"
    semantic_release_id: Mapped[str] = mapped_column(ForeignKey("semantic_releases.id"))
    status: Mapped[str] = mapped_column(String(40))
    manifest: Mapped[dict] = mapped_column(JSONB)
    digest: Mapped[str] = mapped_column(String(64))


class QualityRun(Record, Base):
    __tablename__ = "quality_runs"
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    purpose: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40))
    manifest: Mapped[dict] = mapped_column(JSONB)
    results: Mapped[list] = mapped_column(JSONB, default=list)
    coverage: Mapped[dict] = mapped_column(JSONB, default=dict)
    blockers: Mapped[list] = mapped_column(JSONB, default=list)
    trace: Mapped[list] = mapped_column(JSONB, default=list)


class Finding(Record, Base):
    __tablename__ = "findings"
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("quality_runs.id"))
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.id"))
    title: Mapped[str] = mapped_column(String(180))
    severity: Mapped[str] = mapped_column(String(20))
    layer: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="suspected")
    evidence_ids: Mapped[list] = mapped_column(JSONB)
    reason: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)


class Task(Record, Base):
    __tablename__ = "tasks"
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id"), unique=True)
    state: Mapped[str] = mapped_column(String(40), default="review")
    doctor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    expert_id: Mapped[str | None] = mapped_column(ForeignKey("actors.id"))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scope_manifest: Mapped[dict] = mapped_column(JSONB)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)


class Decision(Record, Base):
    __tablename__ = "decisions"
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    action: Mapped[str] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text)
    before_state: Mapped[str] = mapped_column(String(40))
    after_state: Mapped[str] = mapped_column(String(40))
    manifest: Mapped[dict] = mapped_column(JSONB)


class Signature(Record, Base):
    __tablename__ = "signatures"
    __table_args__ = (UniqueConstraint("task_id", "scope_digest", "role"),)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    role: Mapped[str] = mapped_column(String(30))
    scope_digest: Mapped[str] = mapped_column(String(64))
    manifest: Mapped[dict] = mapped_column(JSONB)
    mode: Mapped[str] = mapped_column(String(40))


class Job(Record, Base):
    __tablename__ = "jobs"
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    case_id: Mapped[str | None] = mapped_column(String(96))
    kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(96))
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    fencing_token: Mapped[int] = mapped_column(Integer, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(96))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EvaluationBatch(Record, Base):
    __tablename__ = "evaluation_batches"
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="frozen")
    manifest: Mapped[dict] = mapped_column(JSONB)
    samples: Mapped[list] = mapped_column(JSONB)
    assignments: Mapped[dict] = mapped_column(JSONB)
    protocol: Mapped[dict] = mapped_column(JSONB)


class Judgment(Record, Base):
    __tablename__ = "judgments"
    __table_args__ = (UniqueConstraint("batch_id", "sample_id", "actor_id"),)
    batch_id: Mapped[str] = mapped_column(ForeignKey("evaluation_batches.id"))
    sample_id: Mapped[str] = mapped_column(String(96))
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    verdict: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    rubric: Mapped[dict] = mapped_column(JSONB)


class Arbitration(Record, Base):
    __tablename__ = "arbitrations"
    __table_args__ = (UniqueConstraint("batch_id", "sample_id", "version"),)
    batch_id: Mapped[str] = mapped_column(ForeignKey("evaluation_batches.id"))
    sample_id: Mapped[str] = mapped_column(String(96))
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    judgment_ids: Mapped[list] = mapped_column(JSONB)
    verdict: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)


class ReleaseRequest(Record, Base):
    __tablename__ = "release_requests"
    stage: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="pending")
    baseline: Mapped[dict] = mapped_column(JSONB)
    conditions: Mapped[list] = mapped_column(JSONB)
    acceptances: Mapped[list] = mapped_column(JSONB, default=list)
    scope: Mapped[dict] = mapped_column(JSONB)


class GateDecision(Record, Base):
    __tablename__ = "gate_decisions"
    request_id: Mapped[str] = mapped_column(ForeignKey("release_requests.id"))
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    outcome: Mapped[str] = mapped_column(String(40))
    evidence: Mapped[dict] = mapped_column(JSONB)
    reason: Mapped[str] = mapped_column(Text)


class Export(Record, Base):
    __tablename__ = "exports"
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    status: Mapped[str] = mapped_column(String(40))
    manifest: Mapped[dict] = mapped_column(JSONB)
    artifact_ref: Mapped[str] = mapped_column(Text)
    digest: Mapped[str] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(40))


class ExportPermit(Record, Base):
    __tablename__ = "export_permits"
    actor_id: Mapped[str] = mapped_column(ForeignKey("actors.id"))
    scope: Mapped[dict] = mapped_column(JSONB)
    kind: Mapped[str] = mapped_column(String(40))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
