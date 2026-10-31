#!/usr/bin/env python3
"""Snapshot or check explicitly listed delivery files; never evaluate behavior."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from datetime import datetime, timezone


class ManifestError(ValueError):
    pass


def require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} 必須是非空文字")


def project_file(root, value):
    require_text(value, "path")
    relative = PurePosixPath(value)
    if (relative.is_absolute() or "\\" in value or ":" in value
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ManifestError(f"路徑必須是規範的項目相對文件路徑: {value}")
    path = root.joinpath(*relative.parts).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ManifestError(f"路徑指向項目根外: {value}") from exc
    if not path.is_file():
        raise ManifestError(f"文件不存在或不是普通文件: {value}")
    return path


def validate_structure(document):
    if not isinstance(document, dict):
        raise ManifestError("清單必須是 JSON 對象")
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        raise ManifestError("schema_version 必須為 1")
    for key in ("project", "release", "scope"):
        require_text(document.get(key), key)
    for key in ("inputs", "artifacts", "omissions"):
        if not isinstance(document.get(key), list):
            raise ManifestError(f"{key} 必須是數組")
    if not document["inputs"] or not document["artifacts"]:
        raise ManifestError("inputs 和 artifacts 均需至少一項")

    identifiers = set()
    for group in ("inputs", "artifacts", "omissions"):
        paths = set()
        for index, item in enumerate(document[group]):
            label = f"{group}[{index}]"
            if not isinstance(item, dict):
                raise ManifestError(f"{label} 必須是對象")
            fields = {"inputs": ("path", "role"),
                      "artifacts": ("id", "title", "path", "audience"),
                      "omissions": ("id", "title", "reason", "next_step")}[group]
            for key in fields:
                require_text(item.get(key), f"{label}.{key}")
            if "id" in fields:
                if item["id"] in identifiers:
                    raise ManifestError(f"交付編號重複: {item['id']}")
                identifiers.add(item["id"])
            if "path" in fields:
                if item["path"] in paths:
                    raise ManifestError(f"{group} 中路徑重複: {item['path']}")
                paths.add(item["path"])
            if group == "artifacts" and item["audience"] not in {"recipient", "internal"}:
                raise ManifestError(f"{label}.audience 必須是 recipient 或 internal")


def fingerprint(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def inspect_files(document, root, manifest, operation):
    errors = []
    for group in ("inputs", "artifacts"):
        for item in document[group]:
            try:
                path = project_file(root, item["path"])
                if path == manifest:
                    raise ManifestError("清單不能引用自身")
                digest, size = fingerprint(path)
                if group == "artifacts" and size == 0:
                    raise ManifestError(f"交付文件為空: {item['path']}")
                if operation == "snapshot":
                    item.update(sha256=digest, bytes=size)
                    continue
                saved_digest = item.get("sha256")
                if not isinstance(saved_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", saved_digest):
                    raise ManifestError(f"缺少有效 SHA-256: {item['path']}")
                if type(item.get("bytes")) is not int or item["bytes"] < 0:
                    raise ManifestError(f"缺少有效文件字節數: {item['path']}")
                if digest != saved_digest or size != item["bytes"]:
                    raise ManifestError(f"文件已變化，需核對版本和證據適用性: {item['path']}")
            except (ManifestError, OSError, RuntimeError) as exc:
                errors.append(f"{group}: {exc}")
    return errors


def save_manifest(path, document):
    """Replace only after the full snapshot has been successfully inspected."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".delivery-manifest-", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temporary.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def process(operation, project, manifest_path):
    result = {"ok": False, "operation": operation, "validation": "files_and_hashes",
              "behavior": "not_evaluated", "recipient_signoff": "not_evaluated",
              "errors": []}
    try:
        root = Path(project).resolve()
        if not root.is_dir():
            raise ManifestError("項目根不存在或不是目錄")
        manifest = project_file(root, manifest_path)
        document = json.loads(manifest.read_text(encoding="utf-8"))
        validate_structure(document)
        result.update(inputs=len(document["inputs"]), artifacts=len(document["artifacts"]),
                      omissions=len(document["omissions"]))
        result["errors"] = inspect_files(document, root, manifest, operation)
        if not result["errors"]:
            if operation == "snapshot":
                document["prepared_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                save_manifest(manifest, document)
            result["ok"] = True
    except json.JSONDecodeError as exc:
        result["errors"] = [f"JSON 格式錯誤: 第 {exc.lineno} 行第 {exc.colno} 列"]
    except (ManifestError, OSError, UnicodeError, RuntimeError) as exc:
        result["errors"] = [str(exc)]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("snapshot", "check"))
    parser.add_argument("--project", required=True, help="實際應用根目錄")
    parser.add_argument("--manifest", required=True, help="相對於應用根的清單 JSON 路徑")
    args = parser.parse_args()
    result = process(args.operation, args.project, args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
