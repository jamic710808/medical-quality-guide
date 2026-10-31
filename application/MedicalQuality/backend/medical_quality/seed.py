"""冪等導入明確標註的工程夾具；不生成真實醫生決定、簽字或專家金標準。"""

from __future__ import annotations

import json


from .common import digest
from .config import PROJECT, settings
from .db import transaction
from .evidence import document_evidence, envelope
from .models import (
    Actor,
    Case,
    Document,
    Evidence,
    Job,
    KnowledgeChunk,
    Rule,
    SemanticRelease,
    Source,
    SourceSnapshot,
)
from .ontology import ONTOLOGY_DIR, native_projection, validate_package
from .quality import create_run
from rdflib import Graph


def seed():
    fixture = json.loads((PROJECT / "backend/fixtures/prototype-synthetic.json").read_text())
    rows = fixture["cases"] + fixture["incoming"]
    folder = settings().artifacts / "synthetic"
    folder.mkdir(parents=True, exist_ok=True)
    with transaction() as db:
        if db.get(Actor, "qc1"):
            print("已有本地業務狀態；未重置任何記錄。")
            return
        case_ids = [r["id"] for r in rows]
        actors = [
            ("qc1", "周瑾 · 質控", "qc", ["A組", "B組"]),
            ("qc2", "沈寧 · 質控", "qc", ["A組"]),
            ("doctor1", "林辰 · 責任醫生", "doctor", ["A組"]),
            ("doctor2", "蘇禾 · 責任醫生", "doctor", ["B組"]),
            ("expert1", "陳一 · 原判專家", "expert", []),
            ("expert2", "何寧 · 原判專家", "expert", []),
            ("expert3", "鄭嵐 · 仲裁專家", "expert", []),
            ("info1", "許程 · 信息科", "info", []),
            ("manager1", "方言 · 管理部門", "manager", []),
            ("support1", "運行支持", "support", []),
        ]
        for actor_id, name, role, groups in actors:
            db.add(
                Actor(
                    id=actor_id,
                    name=name,
                    role=role,
                    groups=groups,
                    case_ids=case_ids if role == "expert" else [],
                    enabled=True,
                )
            )
        db.flush()
        graph = Graph().parse(ONTOLOGY_DIR / "core.ttl", format="turtle")
        ontology, metadata = native_projection(graph)
        validation = validate_package(settings().artifacts / "ontology/semantic-v1")
        manifest = {
            key: digest((ONTOLOGY_DIR / file).read_bytes())
            for key, file in [
                ("core", "core.ttl"),
                ("shapes", "shapes.ttl"),
                ("mappings", "mappings.sssom.tsv"),
                ("bindings", "bindings.json"),
            ]
        }
        manifest.update(
            {
                "value_set": "subject-polarity-temporality-v1",
                "graph_metadata": metadata,
                "package_version": "0.1.0",
                "clinical_review": "pending",
                "native_origin": "local_business_spec",
                "bindings_view": [
                    {
                        "entityTypeId": "PatientRecord",
                        "source": "MIMIC-IV Demo · 候選綁定",
                        "table": "mimic_iv_demo__patients",
                        "columnMappings": {"id": "subject_id"},
                    },
                    {
                        "entityTypeId": "Encounter",
                        "source": "MIMIC-IV Demo · 候選綁定",
                        "table": "mimic_iv_demo__admissions",
                        "columnMappings": {"id": "hadm_id"},
                    },
                ],
            }
        )
        db.add(
            SemanticRelease(
                id="semantic-v1",
                name="醫療質控應用本體 0.1.0",
                status="engineering_ready"
                if validation["profile"] == "pass"
                and validation["elk"] == "pass"
                and validation["shacl_fixture"]
                else "candidate",
                purpose="engineering",
                digest=validation["package_digest"],
                ontology=ontology,
                manifest=manifest,
                validation=validation,
            )
        )
        db.flush()
        concept_refs = [
            ["ClinicalDocument", "DocumentSection"],
            ["PatientRecord", "Encounter"],
            ["ClinicalDocument", "DocumentVersion"],
            ["ObservationRecord", "EvidenceReference"],
            ["ClinicalAssertion", "ClinicalConcept"],
            ["DiagnosticStatement", "ClinicalAssertion"],
            ["MedicationMention", "MedicationConcept"],
            ["DocumentVersion", "SignatureScope"],
        ]
        rule_bytes = json.dumps(fixture["rules"], ensure_ascii=False, indent=2).encode()
        (folder / "rule-candidates-v1.json").write_bytes(rule_bytes)
        rule_source = Source(
            id="rule-candidates-v1",
            name="一期八條文書規則 · 工程候選",
            namespace="medical_quality_rules",
            reference="synthetic:rule-candidates-v1.json",
            format="json",
            data_role="rule_reference",
            data_kind="synthetic",
            purpose="engineering",
            license="項目自建候選規則，臨床適用性尚待專業審核",
            status="success",
            digest=digest(rule_bytes),
            scope={"rules": 8},
            details={"path_base": "synthetic", "origin": "已確認 PRD 與既有原型規則定義"},
        )
        db.add(rule_source)
        db.flush()
        db.add(
            SourceSnapshot(
                source_id=rule_source.id,
                version=1,
                digest=rule_source.digest,
                reference=rule_source.reference,
                manifest={"data_role": "rule_reference", "data_kind": "synthetic"},
            )
        )
        for index, definition in enumerate(fixture["rules"]):
            item = envelope(
                rule_source,
                1,
                "rule-seed",
                "record",
                {"type": "json", "pointer": "/" + str(index)},
                {
                    "value": definition,
                    "text": definition["name"] + " " + definition["issue"] + "。" + definition["advice"],
                },
                transformations=["join_rule_title_and_body"],
            )
            item["id"] = "rule-evidence-" + str(index + 1)
            db.add(
                Evidence(
                    id=item["id"],
                    source_id=rule_source.id,
                    source_version=1,
                    data_role="rule_reference",
                    envelope=item,
                )
            )
            db.flush()
            rule = Rule(
                id=definition["id"] + "-v1",
                rule_key=definition["id"],
                name=definition["name"],
                category=definition["group"],
                severity=definition["risk"],
                status="candidate",
                purpose="engineering",
                semantic_release_id="semantic-v1",
                content=definition["issue"] + "。" + definition["advice"],
                specification={
                    "suggestion": definition["advice"],
                    "concepts": concept_refs[index],
                    "scope": "單內科病區/成人肺炎/出院前文書",
                    "method": definition["method"],
                },
                provenance={
                    "source": "已確認項目八條文書質控需求",
                    "professional_review": "pending",
                    "not_same_as_cmqcic_98": True,
                    "evidence_ids": [item["id"]],
                },
            )
            db.add(rule)
            db.flush()
            db.add(
                KnowledgeChunk(
                    id="chunk-" + str(index + 1),
                    rule_id=rule.id,
                    text=rule.name + " " + rule.content,
                    parent_text=rule.content,
                    evidence_id=item["id"],
                    index_version="mq-rules-v1",
                    embedding=None,
                )
            )
        for row in rows:
            source_id = "synthetic-source-" + row["id"]
            case_id = row["id"]
            owner = "doctor1" if row["team"] == "A組" else "doctor2"
            case = Case(
                id=case_id,
                namespace="synthetic_medical_quality",
                encounter_id=row["record"],
                patient_key="fixture-" + case_id,
                display_name=row["name"],
                group_id=row["team"],
                owner_id=owner,
                data_kind="synthetic",
                status="pending",
                risk="unknown",
                department=row.get("department", "內科一病區"),
                details={
                    "age": row["age"],
                    "sex": row["sex"],
                    "bed": row["bed"],
                    "scope_confirmed": row.get("blocked") != "scope",
                    "required_documents": ["入院記錄", "出院小結"],
                    "discharge_time": "2026-10-13T18:00:00",
                    "report_ids": [] if row["rule"] == 3 else ["CT-001"],
                    "semantic_release_id": "semantic-v1",
                    "rule_ids": [f"MQC-DOC-{i:03d}-v1" for i in range(1, 9)],
                    "fixture_source": "既有產品原型的合成場景；實際狀態由本應用計算和保存",
                },
            )
            db.add(case)
            db.flush()
            documents = []
            for key, title in [("admission", "入院記錄"), ("discharge", "出院小結")]:
                fields = {
                    "encounter_id": row["record"],
                    "recorded_at": "2026-10-12T09:00:00" if key == "admission" else "2026-10-13T16:00:00",
                    "diagnosis_text": "成人肺炎",
                    "course_summary": "按來源記錄診療經過。",
                    "medication_documented": True,
                    "dose_unit": "來源單位已記錄",
                    "author": "合成責任作者",
                    "source_signature": "合成來源簽署字段",
                    "report_refs": ["CT-001"],
                }
                allergy = "藥物過敏史：無。"
                if row["rule"] == 4:
                    allergy = "藥物過敏史：青黴素過敏。" if key == "admission" else "藥物過敏史：否認。"
                if row["rule"] == 0 and key == "discharge":
                    fields["course_summary"] = ""
                if row["rule"] == 1 and key == "discharge":
                    fields["encounter_id"] = "ZY202610-0184"
                if row["rule"] == 2 and key == "discharge":
                    fields["recorded_at"] = "2026-10-14T09:00:00"
                if row["rule"] == 5 and key == "discharge":
                    fields["diagnosis_text"] = "待補充"
                if row["rule"] == 6 and key == "discharge":
                    fields["dose_unit"] = ""
                if row["rule"] == 7 and key == "discharge":
                    fields["author"] = ""
                    fields["source_signature"] = ""
                content = "\n".join(
                    [
                        title,
                        "資料性質：合成工程病例。",
                        f"就診標識：{fields['encounter_id']}。",
                        f"記錄時間：{fields['recorded_at']}。",
                        f"診斷描述：{fields['diagnosis_text']}。",
                        allergy,
                        f"病情變化與診療經過：{fields['course_summary'] or '未填寫'}。",
                        "相關檢查引用：CT-001 胸部檢查報告。",
                        f"用藥記錄：{fields['dose_unit'] or '劑量單位未記錄'}。",
                        f"責任作者：{fields['author'] or '未記錄'}；來源簽署：{fields['source_signature'] or '未關聯'}。",
                    ]
                )
                documents.append({"key": key, "title": title, "fields": fields, "content": content})
            raw = json.dumps(
                {"data_kind": "synthetic", "case": row["record"], "documents": documents},
                ensure_ascii=False,
                indent=2,
            )
            path = folder / (case_id + ".json")
            path.write_text(raw)
            sha = digest(raw.encode())
            source = Source(
                id=source_id,
                name=row["record"] + " 合成文書",
                namespace="synthetic_medical_quality",
                reference="synthetic:" + path.name,
                format="json",
                data_role="business_evidence",
                data_kind="synthetic",
                purpose="engineering",
                license="本項目自建工程夾具，不包含真實患者或專業評測結論",
                status="success",
                digest=sha,
                scope={"case_id": case_id},
                details={"path_base": "synthetic"},
            )
            db.add(source)
            db.flush()
            db.add(
                SourceSnapshot(
                    source_id=source.id,
                    version=1,
                    digest=sha,
                    reference=source.reference,
                    manifest={"data_kind": "synthetic", "scope": source.scope},
                )
            )
            for doc in documents:
                record = Document(
                    id=case_id + "-" + doc["key"] + "-v1",
                    case_id=case_id,
                    document_key=doc["key"],
                    title=doc["title"],
                    content=doc["content"],
                    digest=digest(doc["content"]),
                    author_id="fixture-author",
                    source_id=source.id,
                    fields=doc["fields"],
                )
                db.add(record)
                db.flush()
                document_evidence(db, source, record)
        db.flush()
        actor = db.get(Actor, "qc1")
        for row in rows:
            run = create_run(db, actor, row["id"])
            db.add(Job(actor_id=actor.id, case_id=row["id"], kind="quality", payload={"run_id": run.id}))
    print("已創建 14 個明確合成病例、8 條工程候選規則與獨立本地身份；未生成真人意見、簽字或金標準。")


if __name__ == "__main__":
    seed()
