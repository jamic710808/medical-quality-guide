#!/usr/bin/env python3
"""只在準備階段下載 Docling 資源，運行階段不自動改用雲端。"""

from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil

os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
from docling.utils.model_downloader import download_models

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "artifacts/models/docling"
    download_models(
        output_dir=target,
        with_layout=True,
        with_tableformer=True,
        with_code_formula=False,
        with_picture_classifier=False,
        with_rapidocr=False,
        progress=True,
    )
    package = importlib.util.find_spec("rapidocr_onnxruntime")
    models = Path(package.origin).parent / "models"
    ocr = ROOT / "artifacts/models/rapidocr"
    ocr.mkdir(parents=True, exist_ok=True)
    for source in models.glob("*.onnx"):
        if not (ocr / source.name).exists():
            shutil.copy2(source, ocr / source.name)
    entries = []
    for path in list(target.rglob("*")) + list(ocr.rglob("*")):
        if path.is_file() and ".cache" not in path.parts:
            entries.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    (ROOT / "artifacts/models/ocr-manifest.json").write_text(
        json.dumps(entries, indent=2) + "\n"
    )
    print("本地 Docling / PP-OCRv4 ONNX 資源已準備；模型精度須按具體資料驗證。")


if __name__ == "__main__":
    main()
