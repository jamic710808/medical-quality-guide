#!/usr/bin/env python3
"""Read-only, bounded input and environment reconnaissance; no network or installs."""

from __future__ import annotations

import argparse
import codecs
import csv
import importlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile


SKIP_DIRS = {"node_modules", "__pycache__", "venv", "env", "dist", "build"}
TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".jsonl",
                 ".ndjson", ".xml", ".html", ".htm", ".yaml", ".yml", ".log", ".rst"}
PACKAGES = ("docling", "mineru", "paddleocr", "langextract", "pypdf", "pandas",
            "polars", "pandera", "openpyxl", "xlrd", "markdown-it-py", "torch")
COMMANDS = ("python3", "uv", "pipx", "docling", "mineru", "paddleocr", "ollama",
            "pdftotext", "pdfinfo", "tesseract", "nvidia-smi")


def decode_sample(data: bytes, truncated: bool) -> tuple[str | None, str | None]:
    """Decode strictly; a bounded prefix may end in the middle of a code point."""
    if data.startswith(codecs.BOM_UTF32_LE) or data.startswith(codecs.BOM_UTF32_BE):
        candidates = ["utf-32"]
    elif data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        candidates = ["utf-16"]
    elif b"\0" in data:
        return None, None
    else:
        candidates = ["utf-8-sig", "gb18030"]
    for encoding in candidates:
        try:
            text = codecs.getincrementaldecoder(encoding)(errors="strict").decode(
                data, final=not truncated
            )
            return text, encoding
        except UnicodeError:
            continue
    return None, None


def text_profile(data: bytes, suffix: str, truncated: bool, rows: int) -> dict:
    text, encoding = decode_sample(data, truncated)
    if text is None:
        return {"status": "needs_encoding_or_binary_review"}
    result = {"status": "sampled", "encoding_candidate": encoding,
              "encoding_verified_for": "sample_only", "preview": text[:1000],
              "sample_line_count": len(text.splitlines())}
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        inferred = False
        try:
            delimiter = csv.Sniffer().sniff(text[:8192], delimiters=",\t;|").delimiter
            inferred = True
        except csv.Error:
            pass
        parsed = []
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
        try:
            for row in reader:
                parsed.append(row)
                if len(parsed) >= rows + 1:
                    break
        except csv.Error as exc:
            result["csv_sample_error"] = str(exc)
        result.update({"delimiter_candidate": delimiter, "delimiter_inferred": inferred,
                       "first_record": parsed[0] if parsed else [],
                       "first_record_is_header": "unconfirmed",
                       "sample_records": len(parsed),
                       "sample_column_counts": sorted({len(row) for row in parsed}),
                       "value_types": "strings_preserved",
                       "record_limit": rows + 1,
                       "tail_record_may_be_partial": truncated})
    elif suffix == ".json":
        if truncated:
            result["json_validation"] = "not_checked_incomplete_sample"
        else:
            try:
                value = json.loads(text)
                result["json_validation"] = "valid"
                result["json_root_type"] = type(value).__name__
                if isinstance(value, dict):
                    result["json_keys_preview"] = list(value)[:30]
                elif isinstance(value, list):
                    result["json_array_length"] = len(value)
            except (ValueError, RecursionError) as exc:
                result["json_validation"] = "invalid"
                result["json_error"] = str(exc)[:300]
    elif suffix in {".jsonl", ".ndjson"}:
        lines = text.splitlines()
        if truncated and text and not text.endswith(("\n", "\r")):
            lines = lines[:-1]
        checked, errors = 0, []
        for line_no, line in enumerate(lines, 1):
            if not line.strip():
                continue
            checked += 1
            try:
                json.loads(line)
            except (ValueError, RecursionError):
                errors.append(line_no)
            if checked >= rows:
                break
        result.update({"jsonl_checked_records": checked, "jsonl_invalid_lines": errors,
                       "jsonl_validation_scope": "sample_only"})
    return result


def pdf_profile(path: Path, page_limit: int) -> dict:
    if path.stat().st_size > 32 * 1024 * 1024:
        return {"status": "needs_targeted_pdf_read", "reason": "exceeds_32_MiB_probe_limit"}
    try:
        pypdf = importlib.import_module("pypdf")
    except ImportError:
        return {"status": "needs_pdf_reader", "reason": "pypdf_not_in_current_python"}
    try:
        reader = pypdf.PdfReader(str(path))
        if reader.is_encrypted:
            return {"status": "encrypted", "content_read": False}
        count = len(reader.pages)
        pages = []
        for index in range(min(count, page_limit)):
            extracted = reader.pages[index].extract_text() or ""
            pages.append({"page": index + 1, "extracted_characters": len(extracted),
                          "preview": extracted[:1000]})
        return {"status": "sampled", "page_count": count, "pages": pages,
                "layout_tables_images": "not_checked",
                "ocr_need": "unknown_requires_page_inspection"}
    except Exception as exc:
        return {"status": "pdf_read_failed", "error": str(exc)[:300]}


def inspect_file(path: Path, sample_bytes: int, rows: int, pdf_pages: int) -> dict:
    result = {"path": str(path), "extension": path.suffix.lower()}
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            sample = handle.read(sample_bytes)
        suffix = path.suffix.lower()
        truncated = size > len(sample)
        result.update({"size_bytes": size, "sample_bytes": len(sample),
                       "truncated": truncated, "format_basis": "extension"})
        if sample.startswith(b"%PDF-"):
            result.update({"format": "pdf", "format_basis": "signature",
                           "content": pdf_profile(path, pdf_pages)})
        elif sample.startswith(b"PK\x03\x04"):
            result.update({"format": "zip_container", "format_basis": "signature"})
            if size > 32 * 1024 * 1024:
                result["content"] = {"status": "container_not_inspected_size_limit"}
            else:
                try:
                    with zipfile.ZipFile(path) as archive:
                        names = archive.namelist()
                        if "word/document.xml" in names:
                            result["format"] = "docx_container"
                        elif "xl/workbook.xml" in names:
                            result["format"] = "xlsx_container"
                        elif "ppt/presentation.xml" in names:
                            result["format"] = "pptx_container"
                        result["content"] = {"status": "container_only", "entries": len(names),
                                             "uncompressed_bytes": sum(i.file_size for i in archive.infolist()),
                                             "business_content_read": False}
                except (OSError, zipfile.BadZipFile) as exc:
                    result["content"] = {"status": "container_read_failed", "error": str(exc)[:300]}
        elif sample.startswith(b"\x89PNG\r\n\x1a\n") or sample.startswith(b"\xff\xd8\xff"):
            result.update({"format": "image", "format_basis": "signature",
                           "content": {"status": "needs_visual_or_ocr_read"}})
        elif suffix in TEXT_SUFFIXES:
            result.update({"format": suffix.lstrip("."),
                           "content": text_profile(sample, suffix, truncated, rows)})
        else:
            result.update({"format": suffix.lstrip(".") or "unknown",
                           "content": {"status": "needs_format_specific_read"}})
        if suffix == ".pdf" and result["format"] != "pdf":
            result["format_warning"] = "pdf_extension_without_pdf_signature"
    except OSError as exc:
        result["error"] = str(exc)[:300]
    return result


def inventory(targets: list[Path], max_files: int) -> tuple[list[Path], list[dict], bool]:
    found, skipped, seen = [], [], set()
    protected = Path.home() / ".config/skyforge/credentials.yaml"

    def skip(path: Path, reason: str):
        skipped.append({"path": str(path), "reason": reason})

    def accept(path: Path) -> bool:
        if path.is_symlink():
            skip(path, "symlink_not_followed")
            return False
        resolved = path.resolve()
        if resolved == protected.resolve() or any(part.startswith(".") for part in path.parts if part != "."):
            skip(path, "hidden_or_protected_path")
            return False
        if resolved in seen:
            return False
        seen.add(resolved)
        return True

    for target in targets:
        if target.is_symlink():
            skip(target, "symlink_not_followed")
        elif not target.exists():
            skip(target, "missing")
        elif target.is_file():
            if accept(target):
                if len(found) >= max_files:
                    return found, skipped, True
                found.append(target)
        elif target.is_dir():
            if not accept(target):
                continue
            def walk_error(exc):
                skip(Path(exc.filename or str(target)), "unreadable_directory")
            for root, dirs, names in os.walk(target, followlinks=False, onerror=walk_error):
                base = Path(root)
                kept = []
                for name in sorted(dirs):
                    directory = base / name
                    if name.startswith(".") or name in SKIP_DIRS or directory.is_symlink():
                        skip(directory, "excluded_directory_or_symlink")
                    else:
                        kept.append(name)
                dirs[:] = kept
                for name in sorted(names):
                    path = base / name
                    if accept(path):
                        if not path.is_file():
                            skip(path, "not_regular_file")
                            continue
                        if len(found) >= max_files:
                            return found, skipped, True
                        found.append(path)
        else:
            skip(target, "not_regular_file_or_directory")
    return found, skipped, False


def environment() -> dict:
    packages = {}
    for package in PACKAGES:
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    memory = None
    if platform.system() == "Darwin":
        try:
            proc = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.memsize"],
                                  capture_output=True, text=True, timeout=3, check=True)
            memory = int(proc.stdout.strip())
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    else:
        try:
            memory = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (AttributeError, OSError, ValueError):
            pass
    return {"os": platform.system(), "release": platform.release(), "architecture": platform.machine(),
            "python": {"executable": sys.executable, "version": platform.python_version()},
            "memory_bytes": memory, "disk_free_bytes_at_cwd": shutil.disk_usage(Path.cwd()).free,
            "commands": {name: shutil.which(name) for name in COMMANDS},
            "package_versions_current_python_only": packages,
            "gpu_models_services_credentials": "not_checked",
            "readiness": "discovery_only_not_runtime_verification"}


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--max-files", type=positive, default=500)
    parser.add_argument("--sample-bytes", type=positive, default=65536)
    parser.add_argument("--sample-rows", type=positive, default=25)
    parser.add_argument("--pdf-pages", type=positive, default=3)
    args = parser.parse_args()
    files, skipped, truncated = inventory(args.paths, args.max_files)
    report = {"scope": [str(p) for p in args.paths],
              "limits": {"max_files": args.max_files, "sample_bytes": args.sample_bytes,
                         "sample_rows": args.sample_rows, "pdf_pages": args.pdf_pages,
                         "pdf_container_probe_max_bytes": 32 * 1024 * 1024},
              "inventory_truncated": truncated, "files_selected": len(files),
              "skipped": skipped, "environment": environment(),
              "files": [inspect_file(p, args.sample_bytes, args.sample_rows, args.pdf_pages) for p in files]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if files else 1


if __name__ == "__main__":
    raise SystemExit(main())
