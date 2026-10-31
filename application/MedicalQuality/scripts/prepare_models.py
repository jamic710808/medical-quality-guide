#!/usr/bin/env python3
"""僅在準備期下載公開固定模型；病例處理進程保持離線。"""

from pathlib import Path
import hashlib
import json
import os
import shutil

from huggingface_hub import hf_hub_download, HfApi

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "artifacts/models"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def prepare():
    MODELS.mkdir(parents=True, exist_ok=True)
    # Avoid implicit cached account credentials for public artifacts.
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    selections = [
        (
            "BAAI/bge-m3",
            "5617a9f61b028005a4858fdac845db406aefb181",
            "bge-m3",
            [
                "pytorch_model.bin",
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "sentencepiece.bpe.model",
                "sentence_bert_config.json",
                "modules.json",
                "1_Pooling/config.json",
                "README.md",
            ],
        ),
        (
            "Qwen/Qwen3-4B-GGUF",
            "bc640142c66e1fdd12af0bd68f40445458f3869b",
            "qwen3-4b",
            ["Qwen3-4B-Q4_K_M.gguf", "LICENSE", "README.md"],
        ),
    ]
    manifest = []
    for repo, revision, folder, files in selections:
        info = HfApi(token=False).model_info(
            repo, revision=revision, files_metadata=True
        )
        available = {f.rfilename: f.size for f in info.siblings}
        for name in files:
            if name not in available:
                continue
            dst = MODELS / folder / name
            needed = (
                0
                if dst.exists() and dst.stat().st_size == available[name]
                else available[name]
            )
            if shutil.disk_usage(ROOT).free - needed < 1.5 * 1024**3:
                raise RuntimeError(
                    "磁盤保留空間不足，停止下載；已有資源和原始數據保持不變。"
                )
            print(f"準備 {repo} / {name}", flush=True)
            path = Path(
                hf_hub_download(
                    repo,
                    filename=name,
                    revision=revision,
                    local_dir=MODELS / folder,
                    token=False,
                )
            )
            manifest.append(
                {
                    "repo": repo,
                    "revision": revision,
                    "file": name,
                    "path": str(path.relative_to(ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": sha(path),
                }
            )
            (MODELS / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
            )
    print("固定模型準備完成；運行階段不會自動聯網下載。", flush=True)


if __name__ == "__main__":
    prepare()
