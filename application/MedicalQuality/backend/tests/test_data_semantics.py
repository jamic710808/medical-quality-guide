import gzip
import json
import sqlite3

import pytest
from fastapi import HTTPException
from rdflib import Graph, OWL, RDF

from medical_quality.common import digest
from medical_quality.db import transaction
from medical_quality.evidence import envelope, parse_file, validate_envelope
from medical_quality.models import Evidence, Source
from medical_quality.sources import detect_format, read_database, fixed_records, schema_catalog, source_path
from medical_quality.clinical_context.context import assertions_from_evidence, parse_quantity
from medical_quality.ontology import ONTOLOGY_DIR, import_rdf, validate_assertions, validate_native, resolve


def source(path, fmt, role="business_evidence", kind="synthetic"):
    return Source(
        id="fixture",
        version=1,
        name="格式夾具",
        namespace="test",
        reference=str(path),
        format=fmt,
        data_role=role,
        data_kind=kind,
        purpose="engineering",
        license="自建夾具",
        digest="0" * 64,
    )


def test_csv_logical_rows_duplicates_and_raw_values(tmp_path):
    path = tmp_path / "multi.csv"
    path.write_bytes('id,value,note\n0007,0,"第一行\n第二行"\n0008,,空值\n'.encode("utf-8"))
    result = parse_file(source(path, "csv"), path, 1, "test-csv", {})
    assert result["status"] == "success" and len(result["items"]) == 2
    assert result["items"][0]["locator"]["record_number"] == 1
    assert result["items"][0]["content"]["value"] == ["0007", "0", "第一行\n第二行"]
    assert result["items"][1]["content"]["value"][1] == ""
    duplicate = tmp_path / "duplicate.csv"
    duplicate.write_text("id,id\n1,2\n")
    result = parse_file(source(duplicate, "csv"), duplicate, 1, "dup", {})
    assert result["status"] == "partial" and result["items"][0]["quality"]["status"] == "partial"


def test_json_paths_nested_types_and_jsonl_failures(tmp_path):
    path = tmp_path / "object.json"
    path.write_text(
        json.dumps({"a/b~c": {"zero": 0, "missing": None, "code": "001", "array": [False, {}, []]}})
    )
    result = parse_file(source(path, "json"), path, 1, "json", {})
    assert result["items"][0]["locator"]["pointer"] == "/a~1b~0c"
    assert result["items"][0]["content"]["value"]["code"] == "001"
    assert result["items"][0]["content"]["value"]["array"] == [False, {}, []]
    gz = tmp_path / "rows.jsonl.gz"
    with gzip.open(gz, "wt", encoding="utf-8") as stream:
        stream.write('{"id":"01","text":"同一原文"}\nBAD\n{"id":"02","text":"同一原文"}\n')
    result = parse_file(source(gz, "jsonl.gz"), gz, 1, "jsonl", {})
    assert len(result["items"]) == 2 and result["failures"] == [{"unit": 2, "reason": "invalid_json_record"}]
    assert [e["locator"]["record_number"] for e in result["items"]] == [1, 3]
    assert result["items"][0]["id"] != result["items"][1]["id"]
    assert result["coverage"]["expected_total"] == 3 and result["status"] == "partial"
    limited = parse_file(source(gz, "jsonl.gz"), gz, 1, "limit", {"limit": 1})
    assert limited["coverage"]["expected_total"] is None and limited["coverage"]["truncated"]


def test_markdown_offsets_preserve_unicode_and_heading(tmp_path):
    path = tmp_path / "notes.md"
    raw = "# 入院記錄\n\n過敏史：否認。\n## 檢查\n結果未提供。\n"
    path.write_bytes(raw.encode("utf-8"))
    result = parse_file(source(path, "markdown"), path, 1, "md", {})
    for item in result["items"]:
        loc = item["locator"]
        assert raw[loc["char_start"] : loc["char_end"]] == item["content"]["text"]
        validate_envelope(item)
    assert result["items"][-1]["content"]["metadata"]["heading_path"] == ["入院記錄", "檢查"]


def test_markdown_table_fence_and_crlf_are_retained(tmp_path):
    path = tmp_path / "table.md"
    raw = "# 檢驗\r\n\r\n| 標識 | 值 |\r\n| --- | --- |\r\n| 001 | <0.05 |\r\n\r\n```text\r\n原文指令不是系統命令\r\n```\r\n"
    path.write_bytes(raw.encode())
    result = parse_file(source(path, "markdown"), path, 1, "md-structure", {})
    table = next(i for i in result["items"] if i["kind"] == "table")
    assert table["content"]["rows"][1] == ["001", "<0.05"]
    assert any(i["content"]["metadata"]["block_type"] == "fence" for i in result["items"])
    for item in result["items"]:
        loc = item["locator"]
        assert raw[loc["char_start"] : loc["char_end"]] == item["content"]["text"]


def test_image_and_waveform_metadata_never_claim_diagnosis(tmp_path):
    from PIL import Image

    path = tmp_path / "image.png"
    Image.new("RGB", (64, 48), "white").save(path)
    parsed = parse_file(source(path, "image"), path, 1, "image-meta", {})
    item = parsed["items"][0]
    assert item["kind"] == "image" and item["content"]["metadata"]["width"] == 64
    assert (
        not item["content"]["metadata"]["diagnostic_interpretation"]
        and item["quality"]["modeling_access"] == "restricted"
    )
    header = tmp_path / "record.hea"
    header.write_text(
        "record 2 500 5000\nrecord.dat 16 1000/mV 16 0 0 0 0 I\nrecord.dat 16 1000/mV 16 0 0 0 0 II\n"
    )
    parsed = parse_file(source(header, "waveform"), header, 1, "wave-meta", {})
    item = parsed["items"][0]
    assert item["locator"]["channels"] == ["I", "II"] and item["locator"]["end_sample"] == 5000
    assert (
        not item["content"]["metadata"]["signal_decoded"]
        and not item["content"]["metadata"]["diagnostic_interpretation"]
    )


def test_spreadsheet_preserves_cells_formulas_and_original_types(tmp_path):
    from openpyxl import Workbook

    path = tmp_path / "terms.xlsx"
    book = Workbook()
    sheet = book.active
    sheet.title = "術語映射"
    sheet.append(["標識", "原值", "計算"])
    sheet.append(["001", 0, "=B2+1"])
    sheet["B2"].number_format = "000"
    book.create_sheet("hierarchy")
    book.save(path)
    result = parse_file(source(path, "xlsx"), path, 1, "xlsx-cells", {})
    table = next(x for x in result["items"] if x["locator"]["sheet"] == "術語映射")
    assert table["content"]["rows"][1] == ["001", 0, "=B2+1"]
    assert not table["content"]["metadata"]["formulas_executed"]
    assert (
        next(c for c in table["content"]["metadata"]["cells"] if c["coordinate"] == "B2")["number_format"]
        == "000"
    )
    assert table["quality"]["status"] == "partial"


def test_sqlite_readonly_scope_and_no_invented_foreign_key(tmp_path):
    path = tmp_path / "hospital.sqlite"
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE mimic__encounters (_source_record_number INTEGER PRIMARY KEY, patient_id TEXT, encounter_id TEXT)"
    )
    con.execute('INSERT INTO mimic__encounters VALUES (1,"001","0008")')
    con.commit()
    con.close()
    before = digest(path.read_bytes())
    tables = schema_catalog(path)
    assert tables[0]["identity_scope"] == "snapshot" and not tables[0]["foreign_keys_declared"]
    assert fixed_records(path, "mimic__encounters", 10)[0]["patient_id"] == "001"
    with read_database(path) as con:
        with pytest.raises(sqlite3.DatabaseError):
            con.execute('UPDATE mimic__encounters SET patient_id="99"')
        with pytest.raises(sqlite3.DatabaseError):
            con.execute('ATTACH DATABASE ":memory:" AS elsewhere')
    with pytest.raises(HTTPException):
        fixed_records(path, "mimic__encounters; DROP TABLE mimic__encounters", 10)
    assert digest(path.read_bytes()) == before


def test_format_sniffing_xml_entities_and_path_boundary(tmp_path):
    disguised = tmp_path / "wrong.json"
    disguised.write_bytes(b"%PDF-1.7\n")
    assert detect_format(disguised) == "pdf"
    with pytest.raises(HTTPException):
        source_path("data:../../.config/private")
    xml = tmp_path / "bad.xml"
    xml.write_text('<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>')
    with pytest.raises(Exception):
        parse_file(source(xml, "xml"), xml, 1, "xml", {})
    with pytest.raises(HTTPException):
        import_rdf(xml.read_text(), "xml")


def test_evaluator_and_unknown_source_cannot_enter_modeling(tmp_path):
    p = tmp_path / "x.json"
    for role in ["reference_label", "validation", "heldout"]:
        item = envelope(
            source(p, "json", role),
            1,
            "test",
            "record",
            {"type": "json", "pointer": ""},
            {"value": {"answer": "test"}},
        )
        assert item["quality"]["modeling_access"] == "evaluator_only"
        item["quality"]["modeling_access"] = "allowed"
        with pytest.raises(ValueError):
            validate_envelope(item)
    item = envelope(
        source(p, "json", kind="unknown"), 1, "test", "record", {"type": "json", "pointer": ""}, {"value": 0}
    )
    assert item["quality"]["modeling_access"] == "restricted"


def test_assertion_context_and_units_are_not_patient_truth(tmp_path):
    examples = ["母親曾有青黴素過敏。", "患者否認藥物過敏。", "計劃複查肺炎診斷。", "如果發熱再複查。"]
    evidences = []
    for i, value in enumerate(examples):
        item = envelope(
            source(tmp_path / "x.txt", "text"),
            1,
            "test",
            "text",
            {"type": "text", "line_start": 1, "line_end": 1},
            {"text": value},
        )
        evidences.append(
            Evidence(
                id=str(i),
                source_id="fixture",
                source_version=1,
                data_role="business_evidence",
                document_id="d1",
                envelope=item,
            )
        )
    assertions = assertions_from_evidence(evidences)
    assert assertions[0]["subject"] == "family" and assertions[0]["temporality"] == "historical"
    assert assertions[1]["polarity"] == "negated"
    assert assertions[2]["temporality"] == "planned"
    assert assertions[3]["polarity"] == "hypothetical"
    assert all(a["not_patient_truth"] for a in assertions)
    assert parse_quantity("<0.05 mg/L") == {
        "raw_value": "<0.05 mg/L",
        "value": "0.05",
        "comparator": "<",
        "unit": "mg/L",
        "status": "parsed",
    }
    assert parse_quantity("")["status"] == "unknown" and parse_quantity("0")["value"] == "0"
    assert validate_assertions(assertions)["conforms"]
    assertions[0]["subject"] = "fabricated-role"
    assert not validate_assertions(assertions)["conforms"]


def test_ontology_shape_import_losses_and_fixed_resolution():
    graph = Graph().parse(ONTOLOGY_DIR / "core.ttl", format="turtle")
    assert len(set(graph.subjects(RDF.type, OWL.Class))) == 28
    turtle = """@prefix owl: <http://www.w3.org/2002/07/owl#> . @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      <urn:test:A> a owl:Class ; rdfs:label "同名概念"@zh ; owl:equivalentClass <urn:test:B> .
      <urn:test:B> a owl:Class ; rdfs:label "同名概念"@zh ."""
    imported = import_rdf(turtle, "turtle")
    assert len(imported["ontology"]["entityTypes"]) == 2 and imported["loss_report"]
    invalid = {
        "entityTypes": [{"id": "x", "name": "類型", "description": "定義"}],
        "relationships": [{"id": "edge", "from": "x", "to": "missing"}],
    }
    assert any(i["code"] == "dangling_relation" and i["blocking"] for i in validate_native(invalid))
    with transaction() as db:
        response = resolve(db, "semantic-v1", ["PatientRecord", "不存在的術語"])
        assert response["actual_release"] == "semantic-v1" and response["unsupported"] == ["不存在的術語"]
        with pytest.raises(HTTPException):
            resolve(db, "nonexistent", ["PatientRecord"])


def test_explicit_zero_scope_reads_no_records_and_invalid_limits_are_rejected(tmp_path):
    path = tmp_path / "empty-scope.json"
    path.write_text("not valid JSON; the zero range must never try to parse it")
    value = source(path, "json")
    result = parse_file(value, path, 1, "zero-scope", {"limit": 0})
    assert result["status"] == "empty" and result["items"] == [] and result["failures"] == []
    assert result["coverage"]["expected_total"] == 0 and result["coverage"]["source_total"] is None
    for limit in [-1, 501, 0.5, True, "1"]:
        with pytest.raises(HTTPException) as error:
            parse_file(value, path, 1, "bad-scope", {"limit": limit})
        assert error.value.status_code == 422


def test_five_unit_coverage_keeps_failure_unlocatable_unsupported_and_unknown():
    from medical_quality.evidence import coverage_summary

    results = [
        {"status": "success", "evidence_ids": ["one"]},
        {"status": "success", "evidence_ids": ["two"]},
        {"status": "failed", "failures": [{"reason": "damaged_input"}]},
        {"status": "partial", "failures": [{"reason": "locator_unavailable"}]},
        {"status": "blocked", "failures": [{"reason": "unsupported_format"}]},
    ]
    summary = coverage_summary(results, 5)
    assert summary["expected_total"] == 5 and summary["observed_units"] == 5
    assert summary["counts"] == {
        "success": 2,
        "partial": 1,
        "failed": 1,
        "blocked": 1,
        "empty": 0,
        "not_run": 0,
    }
    assert summary["status"] == "partial" and summary["completion_ratio"] == 2 / 5
    assert coverage_summary([], 0)["status"] == "empty"
    unknown = coverage_summary(results, None)
    assert unknown["expected_total"] is None and unknown["completion_ratio"] is None
    assert coverage_summary(results, 6)["counts"]["not_run"] == 1


