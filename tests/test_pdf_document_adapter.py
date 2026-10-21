from __future__ import annotations

import json

import pytest

from app.agent.adapters.pdf_document_adapter import (
    PdfDocumentAdapter,
    PdfDocumentError,
)


def write_text_pdf(path, page_texts: list[str]) -> bytes:
    """Create a tiny valid PDF with deterministic text streams and no extra dependency."""
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
    }
    page_ids = [3 + (index * 2) for index in range(len(page_texts))]
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_texts)} >>"
    ).encode("ascii")

    font_id = 3 + (2 * len(page_texts))
    for index, text in enumerate(page_texts):
        page_id = 3 + (index * 2)
        content_id = page_id + 1
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET\n".encode("ascii")
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        objects[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"endstream"
        )

    objects[font_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for number in range(1, max(objects) + 1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n".encode("ascii")
        pdf += objects[number] + b"\nendobj\n"

    xref_offset = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    pdf += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode("ascii")
    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    path.write_bytes(pdf)
    return pdf


def adapter_for(root, **limits) -> PdfDocumentAdapter:
    return PdfDocumentAdapter(allowed_roots=(root,), **limits)


def test_pdf_adapter_extracts_each_page_with_alias_and_page_provenance(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "source.pdf"
    original_bytes = write_text_pdf(
        source,
        [
            "Offer reference ABC-123",
            "Window quantity 2",
        ],
    )

    adapter = adapter_for(root)
    result = adapter.extract(source, source_alias="customer-offer-001.pdf")
    payload = result.to_payload()

    assert result.status == "complete"
    assert result.page_count == 2
    assert result.needs_ocr is False
    assert result.pages[0].source_alias == "customer-offer-001.pdf"
    assert result.pages[0].page_number == 1
    assert "ABC-123" in result.pages[0].text
    assert result.pages[1].page_number == 2
    assert "quantity 2" in result.pages[1].text
    assert all(page.extraction_method == "pypdf_text" for page in result.pages)
    assert all(page.extraction_confidence is None for page in result.pages)
    assert payload["ok"] is True

    # Raw customer paths do not cross the semantic payload boundary.
    serialized = json.dumps(payload)
    assert str(root) not in serialized
    assert source.read_bytes() == original_bytes
    assert list(root.iterdir()) == [source]


def test_textless_page_reports_ocr_required_instead_of_successfully_reading_it(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "mixed.pdf"
    write_text_pdf(source, ["Readable page", ""])

    result = adapter_for(root).extract(source)

    assert result.status == "ocr_required"
    assert result.pages[0].needs_ocr is False
    assert result.pages[1].needs_ocr is True
    assert "No text was extracted" in result.pages[1].limitations[0]
    assert result.to_payload()["needs_ocr"] is True


def test_pdf_adapter_rejects_paths_outside_approved_roots(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    outside = tmp_path / "outside.pdf"
    write_text_pdf(outside, ["Do not read"])

    with pytest.raises(PdfDocumentError) as exc_info:
        adapter_for(root).extract(outside)

    assert exc_info.value.code == "path_outside_allowed_roots"
    assert str(tmp_path) not in json.dumps(exc_info.value.to_payload())


def test_pdf_adapter_rejects_traversal_path(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    write_text_pdf(tmp_path / "outside.pdf", ["Do not read"])

    with pytest.raises(PdfDocumentError) as exc_info:
        adapter_for(root).extract(root / ".." / "outside.pdf")

    assert exc_info.value.code == "path_outside_allowed_roots"


def test_pdf_adapter_rejects_unsupported_extension_and_missing_file(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    not_pdf = root / "notes.txt"
    not_pdf.write_text("not a PDF", encoding="utf-8")

    with pytest.raises(PdfDocumentError) as unsupported:
        adapter_for(root).extract(not_pdf)
    assert unsupported.value.code == "unsupported_file_type"

    with pytest.raises(PdfDocumentError) as missing:
        adapter_for(root).extract(root / "missing.pdf")
    assert missing.value.code == "file_not_found"


def test_pdf_adapter_rejects_malformed_pdf_without_disclosing_path(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "broken.pdf"
    source.write_bytes(b"this is not a PDF")

    with pytest.raises(PdfDocumentError) as exc_info:
        adapter_for(root).extract(source)

    assert exc_info.value.code == "invalid_pdf"
    assert str(root) not in json.dumps(exc_info.value.to_payload())


def test_pdf_adapter_enforces_file_page_and_text_budgets(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    one_page = root / "one.pdf"
    pdf_bytes = write_text_pdf(one_page, ["A reasonably sized page"])

    with pytest.raises(PdfDocumentError) as file_limit:
        adapter_for(root, max_file_size_bytes=1).extract(one_page)
    assert file_limit.value.code == "file_size_limit_exceeded"

    many_pages = root / "two.pdf"
    write_text_pdf(many_pages, ["Page one", "Page two"])
    with pytest.raises(PdfDocumentError) as page_limit:
        adapter_for(root, max_pages=1).extract(many_pages)
    assert page_limit.value.code == "page_count_limit_exceeded"

    with pytest.raises(PdfDocumentError) as per_page_limit:
        adapter_for(root, max_page_chars=5).extract(one_page)
    assert per_page_limit.value.code == "page_text_limit_exceeded"

    with pytest.raises(PdfDocumentError) as total_limit:
        adapter_for(root, max_total_chars=5).extract(one_page)
    assert total_limit.value.code == "document_text_limit_exceeded"

    assert one_page.read_bytes() == pdf_bytes


def test_pdf_adapter_rejects_invalid_source_alias_and_limits(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "offer.pdf"
    write_text_pdf(source, ["Test"])

    with pytest.raises(PdfDocumentError) as alias:
        adapter_for(root).extract(source, source_alias="../private.pdf")
    assert alias.value.code == "invalid_source_alias"

    with pytest.raises(ValueError):
        PdfDocumentAdapter(allowed_roots=(root,), max_pages=0)


def test_pdf_adapter_exposes_semantic_descriptor_and_availability(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    adapter = adapter_for(root)

    assert adapter.descriptor.adapter_id == "pdf_document"
    assert adapter.descriptor.application == "PDF"
    assert adapter.supports("extract_text")
    assert adapter.is_available()

def test_pdf_adapter_rejects_encrypted_pdf_without_password_guessing(tmp_path):
    from pypdf import PdfReader, PdfWriter

    root = tmp_path / "approved"
    root.mkdir()
    plaintext = root / "source.pdf"
    write_text_pdf(plaintext, ["Sensitive offer data"])

    reader = PdfReader(plaintext)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("test-password")

    encrypted = root / "encrypted.pdf"
    with encrypted.open("wb") as stream:
        writer.write(stream)

    with pytest.raises(PdfDocumentError) as exc_info:
        adapter_for(root).extract(encrypted)

    assert exc_info.value.code == "encrypted_pdf"
