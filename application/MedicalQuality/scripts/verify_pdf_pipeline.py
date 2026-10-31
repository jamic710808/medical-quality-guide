#!/usr/bin/env python3
"""合成混合/旋轉/續表 PDF 的真實 OCR 與原頁回放。產物只寫 artifacts。"""

import hashlib, io, json, os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from medical_quality.config import settings
from medical_quality.evidence import parse_file
from medical_quality.models import Source

root = settings().artifacts / "verification/pdf-combination"
root.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 32)
images = []
for page_no, rows in [
    (
        1,
        [
            ("檢驗項目", "結果", "單位"),
            ("降鈣素原", "<0.05", "ng/mL"),
            ("過敏記錄", "否認青黴素過敏", "原文"),
        ],
    ),
    (
        2,
        [
            ("檢驗項目", "結果", "單位"),
            ("血紅蛋白", "125", "g/L"),
            ("藥品標識", "0007", "來源編號"),
        ],
    ),
]:
    im = Image.new("RGB", (1200, 1600), "white")
    draw = ImageDraw.Draw(im)
    draw.text(
        (70, 65), f"合成工程掃描 · 跨頁表格 第{page_no}頁", font=font, fill="black"
    )
    draw.text(
        (70, 130),
        "固定樣本，不是患者病歷。續頁不自動拼成同一臨床事件。",
        font=font,
        fill="black",
    )
    xs = [70, 430, 900, 1130]
    ys = [240, 335, 430, 525]
    for x in xs:
        draw.line((x, ys[0], x, ys[-1]), fill="black", width=3)
    for y in ys:
        draw.line((xs[0], y, xs[-1], y), fill="black", width=3)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            draw.text((xs[c] + 12, ys[r] + 26), value, font=font, fill="black")
    images.append(im)
scans = io.BytesIO()
images[0].save(
    scans, format="PDF", save_all=True, append_images=images[1:], resolution=144
)
writer = PdfWriter()
source = (
    settings().data_root / "03_質控規則與參考標註/住院病案首頁數據填寫質量規範-2016.pdf"
)
writer.add_page(PdfReader(source).pages[0])
reader = PdfReader(scans)
writer.add_page(reader.pages[0])
writer.add_page(reader.pages[1].rotate(90))
combined = io.BytesIO()
writer.write(combined)
raw = combined.getvalue()
version = hashlib.sha256(raw).hexdigest()
path = settings().artifacts / "synthetic" / ("pdf-combination-" + version[:20] + ".pdf")
path.parent.mkdir(parents=True, exist_ok=True)
if not path.exists():
    path.write_bytes(raw)
s = Source(
    id="pdf-combination-fixture",
    version=1,
    name="合成混合旋轉表格",
    namespace="engineering_pdf",
    reference="synthetic:" + path.name,
    format="pdf",
    data_role="business_evidence",
    data_kind="synthetic",
    purpose="engineering",
    license="自建工程夾具；首數字頁保留原規範來源",
    digest=version,
)
result = parse_file(s, path, 1, "pdf-combination-final", {"max_pages": 3})
(root / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
text = "\n".join(
    i["content"].get("text", "")
    + " "
    + json.dumps(i["content"].get("rows", []), ensure_ascii=False)
    for i in result["items"]
)
checks = {
    "page_numbers": sorted({i["locator"]["page"] for i in result["items"]}),
    "tables": sum(i["kind"] == "table" for i in result["items"]),
    "negation_preserved": "否認" in text,
    "comparator_preserved": "<0.05" in text,
    "raw_identifier_preserved": "0007" in text,
    "value_preserved": "125" in text,
    "source_sha256": version,
    "source_path": str(path.relative_to(settings().artifacts)),
    "rotated_page": 3,
    "rotation": 90,
    "clinical_qualification": False,
}
(root / "observations.json").write_text(
    json.dumps(checks, ensure_ascii=False, indent=2)
)
print(
    json.dumps(
        {"status": result["status"], "items": len(result["items"]), **checks},
        ensure_ascii=False,
    )
)
