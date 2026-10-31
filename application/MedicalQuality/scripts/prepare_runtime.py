#!/usr/bin/env python3
"""準備固定的本地推理/本體工具；不執行生產部署或讀取已有憑據。"""

from pathlib import Path
import hashlib
import io
import json
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".runtime/tools"
SOURCES = json.loads((Path(__file__).with_name("runtime-sources.json")).read_text())


def download(entry):
    if shutil.disk_usage(ROOT).free - entry["bytes"] < 1.5 * 1024**3:
        raise RuntimeError("保留空間不足，未下載或刪除現有數據。")
    raw = subprocess.run(
        [
            "curl",
            "--fail",
            "--location",
            "--retry",
            "3",
            "--silent",
            "--show-error",
            entry["url"],
        ],
        check=True,
        capture_output=True,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise RuntimeError("固定資源摘要不匹配，未安裝。")
    return raw


def extract(raw, target):
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for item in archive.getmembers():
            if not (target / item.name).resolve().is_relative_to(target.resolve()):
                raise ValueError("資源路徑超出目標目錄")
        archive.extractall(target, filter="data")


def main():
    TOOLS.mkdir(parents=True, exist_ok=True)
    if not (TOOLS / "robot.jar").exists():
        (TOOLS / "robot.jar").write_bytes(download(SOURCES["robot"]))
    if not list(TOOLS.glob("*/Contents/Home/bin/java")):
        extract(download(SOURCES["java"]), TOOLS)
    if not list((TOOLS / "llama").glob("*/llama-server")):
        extract(download(SOURCES["llama"]), TOOLS / "llama")
    (TOOLS / "manifest.json").write_text(
        json.dumps({k: v for k, v in SOURCES.items() if k != "llama"}, indent=2)
    )
    (TOOLS / "llama/manifest.json").write_text(json.dumps(SOURCES["llama"], indent=2))
    print("固定 ROBOT、Temurin 與 llama.cpp 資源已就緒。")


if __name__ == "__main__":
    main()
