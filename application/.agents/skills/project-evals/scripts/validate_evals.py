#!/usr/bin/env python3
"""只讀校驗項目 eval 定義、來源、覆蓋與檢查綁定；不執行測試。"""

import argparse
import json
import re
import sys
from pathlib import Path


FEATURE = re.compile(r"F\d{3}")
AC = re.compile(r"(?m)^#{2,6}\s+(AC-(?:F\d{3}-)?\d{3})\b")
PSC = re.compile(r"(?m)^\|\s*(PSC-\d{3})\s*\|")
CHECK_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}")


def relative_path(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("路徑必須為項目內非空相對路徑")
    path = root / value
    if not path.resolve().is_relative_to(root) or path.resolve() == root:
        raise ValueError(f"路徑越出項目或指向項目根: {value}")
    return path


def strings(value, label, allow_empty=False):
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"{label} 必須為{'可空' if allow_empty else '非空'}字符串數組")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label} 含空值或非字符串")
    return value


def unique_strings(value, label, allow_empty=False):
    values = strings(value, label, allow_empty)
    if len(values) != len(set(values)):
        raise ValueError(f"{label} 含重複值")
    return values


def required_text(obj, key, label):
    if not isinstance(obj.get(key), str) or not obj[key].strip():
        raise ValueError(f"{label} 缺少非空 {key}")


def frontmatter(text):
    lines = text.splitlines()
    result = {}
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip().strip('\"\'')
    return result


def without_fences(text):
    lines, fence = [], None
    for line in text.splitlines():
        mark = re.match(r"^\s*(`{3,}|~{3,})", line)
        if mark:
            token = mark.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None:
            lines.append(line)
    return "\n".join(lines)


def validate_suite(root, name, require_bound):
    suite_path = relative_path(root, name)
    data = json.loads(suite_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("suite 必須為 schema_version: 1 的對象")
    scope = data.get("scope")
    if not isinstance(scope, str) or not (FEATURE.fullmatch(scope) or scope == "product"):
        raise ValueError("scope 必須為 FNNN 或 product")
    sources = unique_strings(data.get("sources"), "sources")
    known_ac, known_psc, target_ac = set(), set(), set()
    kinds = set()
    for source in sources:
        text = relative_path(root, source).read_text(encoding="utf-8")
        meta = frontmatter(text)
        kind = meta.get("document")
        kinds.add(kind)
        authoritative = kind in {"product-prd", "product-spec", "feature-spec", "feature-map"}
        if require_bound and (authoritative or "status" in meta):
            allowed = {"ready"} if kind == "feature-spec" else {"confirmed"}
            if meta.get("status") not in allowed:
                raise ValueError(f"來源尚未確認或 ready: {source}")
        body = without_fences(text)
        ac_ids, psc_ids = [], []
        if kind in {"product-prd", "feature-spec"}:
            ac_ids = AC.findall(body)
            if kind == "feature-spec":
                feature = meta.get("feature", "")
                if not FEATURE.fullmatch(feature):
                    raise ValueError(f"Feature Spec 缺少有效 feature: {source}")
                pattern = rf"AC-{feature}-\d{{3}}"
            else:
                pattern = r"AC-\d{3}"
            if any(not re.fullmatch(pattern, identity) for identity in ac_ids):
                raise ValueError(f"AC 編號與來源文檔類型或 Feature 不符: {source}")
        elif kind == "product-spec":
            psc_ids = PSC.findall(body)
        if len(ac_ids) != len(set(ac_ids)) or len(psc_ids) != len(set(psc_ids)):
            raise ValueError(f"來源重複定義 AC / PSC: {source}")
        if known_ac.intersection(ac_ids) or known_psc.intersection(psc_ids):
            raise ValueError(f"多個來源重複定義 AC / PSC: {source}")
        known_ac.update(ac_ids)
        known_psc.update(psc_ids)
        if kind == "feature-spec" and meta.get("feature") == scope:
            target_ac.update(item for item in ac_ids if item.startswith(f"AC-{scope}-"))
    if not {"product-prd", "product-spec"}.issubset(kinds):
        raise ValueError("sources 必須包含 PRD 和 Product Spec")
    if scope != "product" and not target_ac:
        raise ValueError(f"未找到 {scope} Feature Spec 中定義的 AC")
    contracts = unique_strings(data.get("product_contracts", []), "product_contracts", scope != "product")
    if set(contracts) - known_psc:
        raise ValueError(f"未定義的 product_contracts: {sorted(set(contracts) - known_psc)}")
    if scope != "product" and contracts:
        raise ValueError("product_contracts 僅用於 product 套件")

    cases = data.get("cases")
    checks = data.get("checks")
    if not isinstance(cases, list) or not cases or not isinstance(checks, list):
        raise ValueError("cases 必須非空，checks 必須為數組")
    case_ids, covered_ac, covered_psc = set(), set(), set()
    references, unbound = {}, []
    prefix = scope if scope != "product" else "PRODUCT"
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case 必須為對象")
        identity = case.get("id")
        if not isinstance(identity, str) or not re.fullmatch(rf"EV-{prefix}-\d{{3}}", identity):
            raise ValueError(f"用例 ID 必須為 EV-{prefix}-NNN")
        if identity in case_ids:
            raise ValueError(f"重複用例 ID: {identity}")
        case_ids.add(identity)
        for key in ("title", "given", "when"):
            required_text(case, key, identity)
        strings(case.get("expected"), f"{identity}.expected")
        ac_ids = unique_strings(case.get("source_ac"), f"{identity}.source_ac")
        if set(ac_ids) - known_ac:
            raise ValueError(f"{identity} 引用了未定義的 AC: {sorted(set(ac_ids) - known_ac)}")
        if scope != "product" and not set(ac_ids).intersection(target_ac):
            raise ValueError(f"{identity} 必須關聯本 Feature AC")
        if scope != "product" and any(re.fullmatch(r"AC-F\d{3}-\d{3}", item) and item not in target_ac for item in ac_ids):
            raise ValueError(f"{identity} 跨 Feature AC 應由 product 套件承接")
        covered_ac.update(ac_ids)
        psc_ids = unique_strings(case.get("source_psc", []), f"{identity}.source_psc", scope != "product")
        if set(psc_ids) - known_psc:
            raise ValueError(f"{identity} 引用了未定義的 PSC")
        if scope == "product" and set(psc_ids) - set(contracts):
            raise ValueError(f"{identity} PSC 超出本套件 product_contracts")
        covered_psc.update(psc_ids)
        if "check_ref" not in case:
            raise ValueError(f"{identity} 缺少 check_ref；未綁定應為 null")
        ref = case["check_ref"]
        if ref is None:
            unbound.append(identity)
        elif not isinstance(ref, str) or not CHECK_ID.fullmatch(ref):
            raise ValueError(f"{identity} check_ref 無效")
        else:
            references.setdefault(ref, []).append(identity)
    missing = (target_ac - covered_ac) if scope != "product" else (set(contracts) - covered_psc)
    if missing:
        raise ValueError(f"驗收用例覆蓋缺失: {sorted(missing)}")
    if require_bound and unbound:
        raise ValueError(f"用例尚未綁定檢查: {unbound}")

    output_checks = []
    check_ids = set()
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("check 必須為對象")
        identity = check.get("id")
        if not isinstance(identity, str) or not CHECK_ID.fullmatch(identity):
            raise ValueError("檢查 ID 無效")
        if identity in check_ids:
            raise ValueError(f"重複檢查 ID: {identity}")
        check_ids.add(identity)
        if identity not in references:
            raise ValueError(f"檢查未關聯用例: {identity}")
        method = check.get("method")
        if method == "command":
            strings(check.get("argv"), f"{identity}.argv")
        elif method == "manual":
            for key in ("procedure", "evidence"):
                required_text(check, key, identity)
            if "argv" in check:
                raise ValueError(f"{identity} manual 檢查不能聲明 argv")
        else:
            raise ValueError(f"{identity} method 必須為 command 或 manual")
        inputs = unique_strings(check.get("inputs"), f"{identity}.inputs")
        effective = list(dict.fromkeys([suite_path.relative_to(root).as_posix()] + sources + inputs))
        for value in effective:
            path = relative_path(root, value)
            if require_bound and not path.exists():
                raise ValueError(f"{identity} 檢查輸入不存在: {value}")
            if path.is_dir():
                for child in path.rglob("*"):
                    relative_path(root, child.relative_to(root).as_posix())
        output_checks.append({**check, "case_ids": references[identity], "effective_inputs": effective})
    dangling = set(references) - check_ids
    if dangling:
        raise ValueError(f"check_ref 指向未定義檢查: {sorted(dangling)}")
    return {"suite": name, "scope": scope, "case_ids": sorted(case_ids), "unbound": unbound,
            "checks": output_checks, "covered": sorted(target_ac if scope != "product" else contracts)}


def validate_project(root, suites, require_bound=False):
    root = Path(root).resolve()
    errors, reports = [], []
    scopes, identities, check_ids = set(), set(), set()
    for name in suites:
        try:
            report = validate_suite(root, name, require_bound)
            if report["scope"] in scopes:
                raise ValueError(f"同批重複 scope: {report['scope']}")
            scopes.add(report["scope"])
            ids = set(report["case_ids"])
            checks = {item["id"] for item in report["checks"]}
            if identities.intersection(ids) or check_ids.intersection(checks):
                raise ValueError("同批套件的用例或檢查 ID 重複")
            identities.update(ids)
            check_ids.update(checks)
            reports.append(report)
        except (ValueError, OSError, TypeError) as exc:
            errors.append(f"{name}: {exc}")
    if not suites:
        errors.append("至少選擇一個 suite")
    return {"ok": not errors, "behavior": "not_evaluated", "errors": errors, "suites": reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--suite", action="append", required=True)
    parser.add_argument("--require-bound", action="store_true")
    args = parser.parse_args()
    result = validate_project(args.project, args.suite, args.require_bound)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
