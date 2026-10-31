#!/usr/bin/env python3
"""依據已核查項目結構建設原生五類語義對象；不讀取參考答案。"""

from datetime import datetime, timezone
import json

from medical_quality.config import PROJECT, settings
from medical_quality.native_semantic import call_tool
from medical_quality.ontology import ONTOLOGY_DIR, native_projection
from medical_quality.sources import schema_catalog
from rdflib import Graph


def main():
    workspace = PROJECT / ".evoontology"
    records = {
        "terms": [],
        "mappings": [],
        "relations": [],
        "constraints": [],
        "evidence": [],
    }
    if (workspace / "active.json").exists():
        print("已有原生活動版本；只讀校驗，不覆蓋或重新構建。")
        print(json.dumps(call_tool("validate_semantics", {}), ensure_ascii=False))
        return
    source = settings().data_root / "01_醫院結構化數據/醫院結構化數據.sqlite"
    # Metadata only. No evaluator labels, patient values or private history enter construction.
    tables = schema_catalog(source)
    by_table = {t["table"]: t for t in tables}
    graph = Graph().parse(ONTOLOGY_DIR / "core.ttl", format="turtle")
    ontology, meta = native_projection(graph)
    timestamp = datetime.now(timezone.utc).isoformat()
    records["evidence"].append(
        {
            "id": "ev_product_contract",
            "source": str(ONTOLOGY_DIR / "core.ttl"),
            "query": "讀取已落盤的應用概念/定義、類層級和對象屬性，與 PRD/PSC 清單核對",
            "result": f"應用定義包含 {len(ontology['entityTypes'])} 個類型；臨床映射與生產適用性尚未批准。",
            "validation_method": "項目合同和固定 OWL 定義比對",
            "timestamp": timestamp,
        }
    )
    for node in ontology["entityTypes"]:
        records["terms"].append(
            {
                "id": node["id"],
                "name": node["name"],
                "type": "entity",
                "definition": node["description"],
                "scope": "一期醫療文書質控的工程語義；不是患者事實或醫學診斷",
                "aliases": [node["id"]],
                "evidence": ["ev_product_contract"],
            }
        )
    bindings = json.loads((ONTOLOGY_DIR / "bindings.json").read_text())["bindings"]
    for i, binding in enumerate(bindings):
        table = by_table[binding["table"]]
        if binding["column"] not in {c["name"] for c in table["columns"]}:
            raise ValueError("綁定字段不存在")
        eid = f"ev_schema_{i}"
        records["evidence"].append(
            {
                "id": eid,
                "source": str(source),
                "query": "只讀 pragma_table_info：" + binding["table"],
                "result": json.dumps(
                    {
                        "table": binding["table"],
                        "column": binding["column"],
                        "declared_type": next(
                            c["type"]
                            for c in table["columns"]
                            if c["name"] == binding["column"]
                        ),
                    },
                    ensure_ascii=False,
                ),
                "validation_method": "只讀元數據與數據說明交叉核查；沒有將名稱相似當臨床等價",
                "timestamp": timestamp,
            }
        )
        records["mappings"].append(
            {
                "id": f"mapping_{i}",
                "term_id": binding["concept"],
                "database_source": str(source),
                "table": binding["table"],
                "column": binding["column"],
                "semantic_filter": "限定源命名空間；不合並其他數據集患者",
                "aggregation_semantics": "來源記錄粒度，不等同患者數",
                "grain": binding["grain"],
                "validation": {
                    "description": "物理字段已核對；臨床映射資格仍為候選",
                    "evidence": [eid],
                },
                "confidence": "medium",
            }
        )
    for edge in ontology["relationships"]:
        kind = (
            "hierarchy"
            if edge.get("kind") == "subclass"
            else (
                "composition"
                if edge["id"] in {"partOf", "hasSection"}
                else ("derivation" if edge["id"] == "derivedFrom" else "association")
            )
        )
        # Native hierarchy convention is stated explicitly; no same-value-domain equivalence is inferred.
        records["relations"].append(
            {
                "id": edge["id"],
                "source": edge["to"] if kind == "derivation" else edge["from"],
                "target": edge["from"] if kind == "derivation" else edge["to"],
                "relation_type": kind,
                "connection_condition": "來源/定義關係；不表達未經驗證的臨床因果",
                "description": edge["name"] + "；" + edge.get("description", ""),
                "evidence": ["ev_product_contract"],
            }
        )
    constraints = [
        ("PatientRecord", "來源標識不能跨命名空間合併", ["患者", "身份", "命名空間"]),
        (
            "ClinicalAssertion",
            "來源主張、否定、家屬、時間和不確定性分別保留",
            ["否定", "家屬", "斷言", "既往"],
        ),
        (
            "ObservationRecord",
            "原值、比較符和單位保持；缺失不是零",
            ["單位", "檢驗", "原值"],
        ),
        (
            "SemanticRelease",
            "原生活動版本僅為建設語義，不等於醫療產品批准版本",
            ["本體", "版本", "批准"],
        ),
    ]
    for i, (target, description, keywords) in enumerate(constraints):
        records["constraints"].append(
            {
                "id": f"constraint_{i}",
                "target": target,
                "constraint_type": "scope",
                "trigger_keywords": keywords,
                "severity": "block",
                "scope": "一期來源及文書語義解釋",
                "confidence": "high",
                "description": description,
                "evidence": ["ev_product_contract"],
            }
        )
    project = {
        "schema_version": 1,
        "mode": "rolling_trajectory",
        "data_source": {"type": "sqlite", "path": str(source)},
        "workload_source": {"type": "project_workload", "source": "PRD/PSC 與本體 CQ"},
        "evaluation": {
            "type": "external_evaluator",
            "adapter": "medical_quality_expert",
            "status": "not_run",
        },
        "boundary": {
            "strategy": "rolling_trajectory",
            "construction": "項目需求、只讀結構、合成工程樣本",
            "forbidden": ["參考標註", "留出答案", "專業未授權病例"],
            "clinical_approval": False,
        },
    }
    outputs = {}
    outputs["context"] = call_tool(
        "configure_ontology_project", {"project": project}, construction=True
    )
    questions = [
        {
            "id": "MQ-CQ-01",
            "question": "如何區分來源域內患者身份與就診範圍？",
            "topics": ["身份", "粒度"],
        },
        {
            "id": "MQ-CQ-02",
            "question": "如何回到文書斷言的原始證據及版本？",
            "topics": ["證據", "版本"],
        },
        {
            "id": "MQ-CQ-03",
            "question": "檢驗項目與結果、原值及單位應如何區分？",
            "topics": ["檢驗", "單位"],
        },
        {
            "id": "MQ-CQ-04",
            "question": "本體候選、專業意見和正式簽字分別由什麼對象承接？",
            "topics": ["責任", "本體"],
        },
    ]
    outputs["workload"] = call_tool(
        "prepare_ontology_workload",
        {"questions": questions, "include_history": False, "supplied_only": True},
        construction=True,
    )
    outputs["save"] = call_tool(
        "save_version",
        {"version": "ontology_v0", "records": records},
        construction=True,
    )
    outputs["annotate"] = call_tool(
        "annotate_ontology_version",
        {
            "version": "ontology_v0",
            "summary": "基於已確認應用定義和只讀醫院結構形成的工程語義候選；未讀參考答案，未進行臨床評測。",
            "limitations": [
                "物理字段存在不代表臨床映射獲批",
                "五類對象不能代替完整 OWL/SHACL",
                "未啟用外部受限詞表或臨床自動診斷",
            ],
            "links": [
                {
                    "question_id": "MQ-CQ-01",
                    "object_ids": [
                        "PatientRecord",
                        "Encounter",
                        "mapping_0",
                        "mapping_1",
                    ],
                },
                {
                    "question_id": "MQ-CQ-02",
                    "object_ids": [
                        "EvidenceReference",
                        "DocumentVersion",
                        "ClinicalAssertion",
                    ],
                },
                {
                    "question_id": "MQ-CQ-03",
                    "object_ids": [
                        "ObservationRecord",
                        "ObservationDefinition",
                        "mapping_2",
                    ],
                },
                {
                    "question_id": "MQ-CQ-04",
                    "object_ids": [
                        "SemanticRelease",
                        "HumanDecision",
                        "SignatureScope",
                    ],
                },
            ],
        },
        construction=True,
    )
    outputs["publish"] = call_tool(
        "publish_ontology_build",
        {"version": "ontology_v0", "open_browser": False},
        construction=True,
    )
    outputs["browse"] = call_tool(
        "browse_semantics",
        {"version": "ontology_v0", "query": "文書證據", "kind": "all", "limit": 6},
    )
    outputs["resolve"] = call_tool(
        "resolve_semantics",
        {
            "version": "ontology_v0",
            "mentions": ["PatientRecord", "Encounter"],
            "context": "來源身份與就診粒度",
        },
    )
    folder = settings().artifacts / "verification"
    folder.mkdir(exist_ok=True, parents=True)
    (folder / "native-semantic-build.json").write_text(
        json.dumps(outputs, ensure_ascii=False, indent=2)
    )
    print("原生 MCP 建設、校驗、激活及固定版本 browse/resolve 已實際調用；僅工程語義。")


if __name__ == "__main__":
    main()
