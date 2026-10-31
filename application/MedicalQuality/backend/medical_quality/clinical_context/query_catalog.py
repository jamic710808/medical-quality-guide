"""固定粒度的只讀醫院數據查詢；不接受 SQL 或任意表/字段。"""

from sqlalchemy.orm import Session
from ..access import require
from ..common import audit, fail
from ..models import Actor, Source
from ..sources import read_database, source_for_read


def query(db: Session, actor: Actor, source_id: str, operation: str, parameters: dict):
    require(actor, "cases", purpose="research")
    source = db.get(Source, source_id)
    if not source:
        fail("source_missing", "來源不可用。", 404)
    source, path = source_for_read(db, actor, source.id, source.version)
    if source.format != "sqlite":
        fail("source_format", "該入口要求已登記只讀結構庫。", 422)
    namespace = parameters.get("namespace", "mimic_iv_demo")
    if namespace != "mimic_iv_demo":
        fail("mapping_not_supported", "該來源命名空間尚無經核對查詢模板，不能沿用其他來源鍵。", 422)
    limit = max(1, min(int(parameters.get("limit", 20)), 100))
    with read_database(path) as connection:
        if operation == "list_encounters":
            rows = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM mimic_iv_demo__admissions ORDER BY hadm_id LIMIT ?", (limit + 1,)
                )
            ]
            count = connection.execute(
                'SELECT COUNT(DISTINCT hadm_id) FROM mimic_iv_demo__admissions WHERE hadm_id IS NOT NULL AND hadm_id != ""'
            ).fetchone()[0]
            patients = connection.execute(
                'SELECT COUNT(DISTINCT subject_id) FROM mimic_iv_demo__admissions WHERE subject_id IS NOT NULL AND subject_id != ""'
            ).fetchone()[0]
            result = {
                "operation": operation,
                "unit": "source_encounter",
                "items": rows[:limit],
                "has_more": len(rows) > limit,
                "encounter_count": count,
                "patient_count": patients,
                "namespace": namespace,
            }
        elif operation == "encounter_context":
            encounter = str(parameters.get("encounter_id", ""))
            if not encounter or len(encounter) > 96:
                fail("encounter_id", "請提供原始就診標識。", 422)
            matches = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM mimic_iv_demo__admissions WHERE hadm_id=? LIMIT 3", (encounter,)
                )
            ]
            if len(matches) != 1:
                return {
                    "operation": operation,
                    "status": "ambiguous" if matches else "not_found",
                    "namespace": namespace,
                    "source_version": source.version,
                    "matches": len(matches),
                    "not_patient_diagnosis": True,
                }
            admission = matches[0]
            subject = admission["subject_id"]
            patients = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM mimic_iv_demo__patients WHERE subject_id=? LIMIT 3", (subject,)
                )
            ]
            labs = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM mimic_iv_demo__labevents WHERE hadm_id=? AND subject_id=? ORDER BY _source_record_number LIMIT ?",
                    (encounter, subject, limit + 1),
                )
            ]
            count = connection.execute(
                "SELECT COUNT(*) FROM mimic_iv_demo__labevents WHERE hadm_id=? AND subject_id=?",
                (encounter, subject),
            ).fetchone()[0]
            unlinked = connection.execute(
                'SELECT COUNT(*) FROM mimic_iv_demo__labevents WHERE subject_id=? AND (hadm_id IS NULL OR hadm_id="")',
                (subject,),
            ).fetchone()[0]
            definitions = {}
            for item_id in {r["itemid"] for r in labs[:limit]}:
                values = [
                    dict(r)
                    for r in connection.execute(
                        "SELECT * FROM mimic_iv_demo__d_labitems WHERE itemid=? LIMIT 3", (item_id,)
                    )
                ]
                definitions[item_id] = {
                    "records": values,
                    "status": "resolved" if len(values) == 1 else "ambiguous_or_missing",
                }
            result = {
                "operation": operation,
                "status": "partial" if len(patients) != 1 or unlinked else "resolved",
                "namespace": namespace,
                "encounter": admission,
                "patient_records": patients,
                "patient_identity_status": "source_linked" if len(patients) == 1 else "ambiguous",
                "observations": labs[:limit],
                "observation_count": count,
                "observation_definitions": definitions,
                "unlinked_observation_count_for_subject": unlinked,
                "has_more": len(labs) > limit,
                "time_basis": "source_deidentified_shifted_calendar",
                "age_basis": "anchor_age，不是任意就診的精確年齡",
                "not_patient_diagnosis": True,
                "mapping_status": "verified_source_keys_not_clinical_equivalence",
            }
        else:
            fail("query_operation", "未登記的查詢操作。", 422)
    result["source_id"] = source.id
    result["source_version"] = source.version
    result["consistency"] = "同一只讀連接中的固定文件範圍；不宣稱活躍外部數據庫的全庫同時刻快照"
    audit(
        db,
        actor,
        "source.structured_query",
        source.id,
        purpose="research",
        details={"operation": operation, "namespace": namespace, "limit": limit},
    )
    return result
