from __future__ import annotations

from functools import lru_cache
import re

import jieba
import numpy as np
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from .access import require
from .common import audit, digest, fail, public
from .config import settings
from .models import Actor, Job, KnowledgeChunk, KnowledgeIndex, Outbox, Rule, now
from .db import transaction
from .access import refresh_actor
from .ontology import get_release

TOKENIZER_VERSION = "jieba-0.42.1+mq-terms-v1"
for term in ["病歷", "過敏史", "就診標識", "證據定位", "病情變化", "責任簽字", "出院小結", "入院記錄"]:
    jieba.add_word(term)


def tokenize(text: str) -> list[str]:
    return [x.lower() for x in jieba.cut(text) if x.strip()]


def reciprocal_rank_fusion(lists: list[list[str]], k=60) -> dict[str, float]:
    result = {}
    for sequence in lists:
        for rank, key in enumerate(dict.fromkeys(sequence), 1):
            result[key] = result.get(key, 0) + 1 / (k + rank)
    return result


@lru_cache(maxsize=1)
def embedding_model():
    path = settings().artifacts / "models/bge-m3"
    if not (path / "config.json").exists():
        raise RuntimeError("embedding_model_unavailable")
    import os

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from FlagEmbedding import BGEM3FlagModel

    return BGEM3FlagModel(str(path), use_fp16=False, devices="cpu")


def embed(texts: list[str]) -> np.ndarray:
    data = embedding_model().encode(
        texts,
        batch_size=4,
        max_length=1024,
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )["dense_vecs"]
    array = np.asarray(data, dtype=np.float32)
    if (
        array.ndim != 2
        or array.shape[1] != 1024
        or not np.isfinite(array).all()
        or np.any(np.linalg.norm(array, axis=1) == 0)
    ):
        raise ValueError("embedding_invalid")
    return array / np.linalg.norm(array, axis=1, keepdims=True)


def semantic_expansion(query: str, release) -> dict:
    terms = []
    paths = []
    metadata = release.manifest.get("graph_metadata", {}).get("node_meta", {})
    for node in release.ontology["entityTypes"]:
        approved = release.status == "approved" or (
            release.status == "engineering_ready" and release.purpose == "engineering"
        )
        if not approved:
            continue
        aliases = metadata.get(node["id"], {}).get("approved_aliases", [])
        labels = [node["name"], node["id"], *aliases]
        if any(label and label.lower() in query.lower() for label in labels):
            for value in labels:
                if value not in terms:
                    terms.append(value)
            paths.append(
                {
                    "concept_id": node["id"],
                    "original_iri": node.get("iri") or metadata.get(node["id"], {}).get("original_iri"),
                    "relation": "fixed_label_or_approved_alias",
                    "release_id": release.id,
                }
            )
        if len(paths) >= 3:
            break
    return {
        "original_query": query,
        "expanded_query": query + " " + " ".join(terms[:6]) if terms else query,
        "terms": terms[:6],
        "paths": paths,
        "used_for": "retrieval_only_not_patient_facts",
    }


def retrieve(
    db: Session,
    actor: Actor,
    query: str,
    release_id: str,
    *,
    purpose="engineering",
    limit=8,
    require_dense=False,
    index_id=None,
    rule_id=None,
):
    require(actor, "knowledge", purpose=purpose)
    release = get_release(db, release_id, purpose)
    eligible = ["candidate", "approved"] if purpose != "production" else ["approved"]
    rules = db.scalars(
        select(Rule).where(
            Rule.semantic_release_id == release.id, Rule.status.in_(eligible), Rule.purpose == purpose
        )
    ).all()
    if rule_id:
        rules = [r for r in rules if r.id == rule_id]
    exact = re.fullmatch(r"MQC-DOC-\d{3}", query.strip(), re.I)
    if exact:
        matches = [r for r in rules if r.rule_key == query.upper()]
        return {
            "mode": "exact_id",
            "query": query,
            "semantic_release_id": release.id,
            "results": [
                {
                    "rule": public(r),
                    "rank": i + 1,
                    "score": None,
                    "evidence_ids": r.provenance.get("evidence_ids", []),
                }
                for i, r in enumerate(matches)
            ],
            "gaps": [] if matches else ["rule_version_not_eligible"],
        }
    index = (
        db.get(KnowledgeIndex, index_id)
        if index_id
        else db.scalar(
            select(KnowledgeIndex)
            .where(KnowledgeIndex.semantic_release_id == release.id, KnowledgeIndex.status == "ready")
            .order_by(KnowledgeIndex.created_at.desc())
        )
    )
    if index_id and (not index or index.status != "ready" or index.semantic_release_id != release.id):
        return {
            "mode": "blocked",
            "results": [],
            "gaps": ["index_version_unavailable"],
            "semantic_release_id": release.id,
        }
    stmt = select(KnowledgeChunk).where(KnowledgeChunk.rule_id.in_([r.id for r in rules]))
    if index:
        stmt = stmt.where(KnowledgeChunk.index_version == index.id)
    else:
        stmt = stmt.where(KnowledgeChunk.index_version == "mq-rules-v1")
    chunks = db.scalars(stmt).all()
    if not chunks:
        return {
            "mode": "empty",
            "results": [],
            "gaps": ["no_eligible_knowledge"],
            "semantic_release_id": release.id,
        }
    expansion = semantic_expansion(query, release)
    tokens = tokenize(expansion["expanded_query"])
    corpus = [tokenize(c.text) for c in chunks]
    scores = BM25Okapi(corpus).get_scores(tokens)
    # Zero/negative IDF in a small corpus must not admit documents with no lexical match.
    matched = [i for i, c in enumerate(corpus) if set(tokens) & set(c)]
    lexical = sorted(matched, key=lambda i: (-float(scores[i]), chunks[i].id))[:20]
    dense = []
    dense_scores = {}
    gaps = []
    mode = "lexical_only"
    if all(c.embedding is not None for c in chunks):
        try:
            vector = embed([expansion["expanded_query"]])[0]
            allowed = [c.id for c in chunks]
            rows = db.execute(
                select(
                    KnowledgeChunk.id,
                    KnowledgeChunk.embedding.cosine_distance(vector.tolist()).label("distance"),
                )
                .where(KnowledgeChunk.id.in_(allowed))
                .order_by("distance")
                .limit(20)
            ).all()
            dense = [row.id for row in rows]
            dense_scores = {row.id: 1 - float(row.distance) for row in rows}
            mode = "hybrid"
        except (ImportError, RuntimeError, ValueError):
            gaps.append("embedding_unavailable")
    else:
        gaps.append("dense_index_not_built")
    if require_dense and mode != "hybrid":
        return {"mode": "blocked", "results": [], "gaps": gaps, "semantic_release_id": release.id}
    lexical_ids = [chunks[i].id for i in lexical]
    fused = reciprocal_rank_fusion([lexical_ids, dense] if dense else [lexical_ids])
    by_id = {c.id: c for c in chunks}
    by_rule = {r.id: r for r in rules}
    results = []
    for key in sorted(fused, key=lambda k: (-fused[k], k))[: min(limit, 20)]:
        chunk = by_id[key]
        rank = lexical_ids.index(key) + 1 if key in lexical_ids else None
        results.append(
            {
                "id": key,
                "text": chunk.text,
                "parent_text": chunk.parent_text,
                "rule": public(by_rule[chunk.rule_id]),
                "evidence_id": chunk.evidence_id,
                "rrf_score": fused[key],
                "lexical_rank": rank,
                "dense_rank": dense.index(key) + 1 if key in dense else None,
                "dense_score": dense_scores.get(key),
                "index_version": chunk.index_version,
                "confidence": None,
            }
        )
    return {
        "mode": mode,
        "query": query,
        "semantic_expansion": expansion,
        "results": results,
        "gaps": gaps,
        "semantic_release_id": release.id,
        "index_version": index.id if index else "mq-rules-v1",
        "tokenizer_version": TOKENIZER_VERSION,
        "score_meaning": "檢索排序分數，不是醫學概率",
    }


def build_index(actor_id: str, release_id="semantic-v1", lease=None):
    """Compute outside the transaction, then publish a complete immutable generation."""
    with transaction() as db:
        actor = refresh_actor(db, actor_id)
        require(actor, "knowledge_edit")
        release = get_release(db, release_id)
        rules = db.scalars(
            select(Rule).where(
                Rule.semantic_release_id == release.id, Rule.status.in_(["candidate", "approved"])
            )
        ).all()
        records = [
            {
                "rule_id": r.id,
                "rule_version": r.version,
                "policy_version": r.policy_version,
                "text": r.name + " " + r.content,
                "parent_text": r.content,
                "evidence_id": r.provenance.get("evidence_ids", [None])[0],
            }
            for r in rules
        ]
        if not records:
            fail("no_eligible_rules", "沒有可建立索引的規則。")
        manifest = {
            "semantic_release_id": release.id,
            "semantic_digest": release.digest,
            "records": records,
            "model": "BAAI/bge-m3",
            "model_revision": "5617a9f61b028005a4858fdac845db406aefb181",
            "dimensions": 1024,
            "tokenizer": TOKENIZER_VERSION,
            "normalization": "l2",
            "metric": "cosine_exact",
        }
        fingerprint = digest(manifest)
        existing = db.scalar(
            select(KnowledgeIndex).where(
                KnowledgeIndex.digest == fingerprint, KnowledgeIndex.status == "ready"
            )
        )
        if existing:
            return {"id": existing.id, "status": "ready", "reused": True}
    vectors = embed([r["text"] for r in records])
    index_id = "index-" + fingerprint[:24]
    artifact = settings().artifacts / "retrieval" / index_id
    artifact.mkdir(parents=True, exist_ok=True)
    import json

    (artifact / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    with transaction() as db:
        actor = refresh_actor(db, actor_id)
        require(actor, "knowledge_edit")
        get_release(db, release_id)
        if lease:
            job = db.scalar(select(Job).where(Job.id == lease["id"]).with_for_update())
            if (
                not job
                or job.fencing_token != lease["token"]
                or job.status != "running"
                or job.lease_until <= now()
            ):
                fail("stale_worker", "舊索引嘗試不可發佈。")
        db.execute(
            __import__("sqlalchemy").text("SELECT pg_advisory_xact_lock(:k)"),
            {"k": int(fingerprint[:15], 16)},
        )
        if db.get(KnowledgeIndex, index_id):
            return {"id": index_id, "status": "ready", "reused": True}
        for record, vector in zip(records, vectors):
            rule = db.get(Rule, record["rule_id"])
            if (
                not rule
                or rule.status not in {"candidate", "approved"}
                or rule.version != record["rule_version"]
                or rule.policy_version != record["policy_version"]
            ):
                fail("index_input_changed", "索引生成期間規則資格變化，未發佈候選索引。")
            db.add(
                KnowledgeChunk(
                    id=digest([index_id, rule.id])[:32],
                    rule_id=rule.id,
                    evidence_id=record["evidence_id"],
                    text=record["text"],
                    parent_text=record["parent_text"],
                    embedding=vector.tolist(),
                    index_version=index_id,
                    embedding_model=manifest["model"] + "@" + manifest["model_revision"],
                )
            )
        db.add(
            KnowledgeIndex(
                id=index_id,
                semantic_release_id=release_id,
                status="ready",
                manifest=manifest,
                digest=fingerprint,
            )
        )
        db.add(
            Outbox(
                kind="knowledge.index.published",
                aggregate_id=index_id,
                payload={"semantic_release_id": release_id, "digest": fingerprint},
            )
        )
        audit(
            db,
            actor,
            "knowledge.index.publish",
            index_id,
            details={"count": len(records), "digest": fingerprint, "semantic_release_id": release_id},
        )
    return {"id": index_id, "status": "ready", "chunks": len(records), "dimensions": 1024}
