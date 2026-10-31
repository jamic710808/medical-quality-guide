#!/usr/bin/env python3
"""複用標準需求看板模板，補齊項目品牌，生成可離線打開的單文件。"""

import base64
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import tempfile


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
WORKSPACE = PROJECT.parent


def main():
    input_path = HERE / "board-data.json"
    title = json.loads(input_path.read_text(encoding="utf-8"))["project"]["title"]
    logo = (PROJECT / "frontend/public/brand/ff-logo.png").read_bytes()
    if hashlib.sha256(logo).hexdigest() != "522944bbaee48d98190c8c5a0a0ac80f05b71b1975838807742a782e2aeceedc":
        raise ValueError("FF Logo 與項目約定不一致")

    generator = WORKSPACE / ".agents/skills/review-project-requirements/scripts/build_board.py"
    spec = importlib.util.spec_from_file_location("requirement_board", generator)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory(prefix="medicalquality-board-") as temporary:
        rendered = Path(temporary) / "index.html"
        module.build(input_path, rendered)
        page = rendered.read_text(encoding="utf-8")

    brand = f'<div class="brand">{html.escape(title)}</div>'
    if page.count(brand) != 1 or page.count("</style>") != 1 or page.count("</footer>") != 1:
        raise ValueError("標準看板模板發生變化，請核對品牌插入位置")
    encoded_logo = base64.b64encode(logo).decode("ascii")
    page = page.replace(brand, (
        '<div class="brand">'
        f'<img class="ff-logo" src="data:image/png;base64,{encoded_logo}" '
        f'alt="{html.escape(title, quote=True)} Logo" width="32" height="32">'
        f'<span>{html.escape(title)}</span></div>'
    ))
    page = page.replace("</style>", (
        '.brand:before{display:none}.ff-logo{display:block;flex:0 0 32px;object-fit:contain}'
        '.brand-signature{padding-top:12px;border-top:1px solid #dce3dc;'
        'font-size:13px;color:#5a7565}'
        '@media(max-width:1050px){.reading-controls{flex:1 1 100%;min-width:0}}\n</style>'
    ))
    page = page.replace("</footer>", '<p class="brand-signature">@賦範空間 獨家研發</p></footer>')
    output = HERE / "index.html"
    output.write_text(page, encoding="utf-8")
    print(f"項目 Playground 已生成：{output}")


if __name__ == "__main__":
    main()
