import io, json
from uuid import uuid4
from PIL import Image
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from medical_quality.config import settings
from medical_quality.db import transaction
from medical_quality.access import refresh_actor
from medical_quality.sources import register
from medical_quality.evidence import envelope
from medical_quality.models import Evidence
from conftest import login


def test_rotated_page_geometry_authorization_and_changed_source(client):
    key = "page-" + uuid4().hex
    root = settings().artifacts
    path = root / "uploads" / (key + ".pdf")
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = io.BytesIO()
    writer = canvas.Canvas(stream, pagesize=(600, 800))
    writer.drawString(80, 700, "SYNTHETIC: NEGATED, <0.05, 0007")
    writer.save()
    pdf = PdfWriter()
    pdf.add_page(PdfReader(stream).pages[0].rotate(90))
    pdf.write(path)
    native = root / "parsing" / key / "docling.json"
    native.parent.mkdir(parents=True, exist_ok=True)
    native.write_text(
        json.dumps(
            {
                "pages": {"1": {"size": {"width": 800, "height": 600}}},
                "texts": [{"text": "SYNTHETIC", "prov": [{"page_no": 1}]}],
            }
        )
    )
    try:
        with transaction() as db:
            actor = refresh_actor(db, "qc1")
            source = register(
                db,
                actor,
                upload={
                    "reference": "upload:" + path.name,
                    "namespace": "pdf_geometry_fixture",
                    "name": "旋轉原頁工程夾具",
                    "kind": "synthetic",
                    "role": "business_evidence",
                    "license": "自建夾具",
                },
            )
            from medical_quality.models import Source

            source_obj = db.get(Source, source["id"])
            item = envelope(
                source_obj,
                1,
                key,
                "text",
                {"type": "pdf", "page": 1, "bbox": [100, 100, 400, 120], "unit": "pt", "origin": "top_left"},
                {
                    "text": "SYNTHETIC",
                    "payload_ref": str(native.relative_to(root)),
                    "metadata": {"native_ref": "#/texts/0"},
                },
            )
            evidence = Evidence(
                id=item["id"],
                source_id=source["id"],
                source_version=1,
                data_role="business_evidence",
                envelope=item,
            )
            db.add(evidence)
            eid = evidence.id
        login(client, "qc1")
        detail = client.get("/api/v1/evidence/" + eid)
        assert detail.status_code == 200, detail.text
        response = client.get("/api/v1/evidence/" + eid + "/page-image")
        assert response.status_code == 200, response.text
        picture = Image.open(io.BytesIO(response.content)).convert("RGB")
        assert picture.size == (1200, 900) and picture.getpixel((150, 150)) == (0, 122, 255)
        assert "no-store" in response.headers["cache-control"]
        login(client, "info1")
        assert client.get("/api/v1/evidence/" + eid + "/page-image").status_code == 404
        with transaction() as db:
            refresh_actor(db, "qc1")
            db.get(Evidence, eid).case_id = "C001"
        login(client, "doctor1")
        cropped = client.get("/api/v1/evidence/" + eid + "/page-image")
        assert cropped.status_code == 200 and Image.open(io.BytesIO(cropped.content)).size[1] < 900
        login(client, "qc1")
        path.write_bytes(b"changed")
        assert client.get("/api/v1/evidence/" + eid + "/page-image").status_code == 409
    finally:
        path.unlink(missing_ok=True)
        native.unlink(missing_ok=True)
