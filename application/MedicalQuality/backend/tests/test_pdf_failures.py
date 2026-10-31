import socket
from pypdf import PdfWriter
from medical_quality.evidence import parse_file
from test_data_semantics import source


def test_corrupt_and_over_budget_pdf_fail_without_external_fallback(tmp_path, monkeypatch):
    calls = []
    original = socket.socket.connect

    def connect(sock, address):
        if isinstance(address, tuple) and address[0] not in ["127.0.0.1", "::1", "localhost"]:
            calls.append(address[0])
            raise AssertionError("no external processing permitted")
        return original(sock, address)

    monkeypatch.setattr(socket.socket, "connect", connect)
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"%PDF-1.7\ncorrupt synthetic file")
    broken = parse_file(source(bad, "pdf"), bad, 1, "broken-pdf", {})
    assert broken["status"] != "success" and not broken["items"] and broken["failures"]
    large = tmp_path / "over-budget.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=600, height=800)
    writer.add_blank_page(width=600, height=800)
    writer.write(large)
    limited = parse_file(source(large, "pdf"), large, 1, "over-budget-pdf", {"max_pages": 1})
    assert limited["status"] != "success" and not limited["items"] and limited["failures"]
    assert calls == []
