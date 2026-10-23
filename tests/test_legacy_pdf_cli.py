from __future__ import annotations

import importlib
import json
from pathlib import Path
import socket
import sys

import pytest

from app.agent.adapters.pdf_document_adapter import PdfDocumentError
from app.ai import analyze_pdf as legacy_pdf


def write_text_pdf(path: Path, page_texts: list[str]) -> bytes:
    """Create a compact deterministic PDF fixture with text and optional blank pages."""
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
    }
    page_ids = [3 + index * 2 for index in range(len(page_texts))]
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_texts)} >>".encode("ascii")
    font_id = 3 + (2 * len(page_texts))

    for index, text in enumerate(page_texts):
        page_id = 3 + index * 2
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


def test_import_is_safe_and_does_not_create_fixed_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert importlib.reload(legacy_pdf) is legacy_pdf
    assert list(tmp_path.iterdir()) == []
    assert not hasattr(legacy_pdf, "client")


def test_analyze_pdf_returns_page_attributed_facts_and_local_validation(tmp_path):
    approved = tmp_path / "approved"
    approved.mkdir()
    source = approved / "offer.pdf"
    original = write_text_pdf(
        source,
        [
            "Produkt: okno\nSzerokość: 1200 mm\nWysokość: 1500 mm\nIlość: 2 szt.",
            "Notatka bez rozpoznawanych pól",
        ],
    )

    result = legacy_pdf.analyze_pdf(
        source,
        allowed_roots=(approved,),
        source_alias="offer-source",
    )

    assert result["ok"] is True
    assert result["status"] == "validated"
    assert result["source"]["alias"] == "offer-source"
    assert result["source"]["page_count"] == 2
    assert result["source"]["pages"][0]["page_number"] == 1
    assert result["source"]["pages"][1]["needs_ocr"] is False
    facts = result["quote_facts"]["facts"]
    by_field = {fact["field_name"]: fact for fact in facts}
    assert by_field["product_type"]["raw_value"] == "okno"
    assert by_field["width"]["source"]["page_number"] == 1
    assert by_field["width"]["source"]["source_alias"] == "offer-source"
    assert by_field["width"]["evidence_text"] == "Szerokość: 1200 mm"
    assert by_field["height"]["raw_value"] == "1500 mm"
    assert by_field["quantity"]["normalized_value"] == 2
    assert result["validation"]["can_execute"] is True
    assert result["validation"]["normalized_values"]["width"] == 1200
    assert result["side_effects"] == {
        "model_calls": 0,
        "network_calls": 0,
        "gui_actions": 0,
        "source_files_modified": 0,
    }
    assert source.read_bytes() == original
    assert list(approved.iterdir()) == [source]
    assert str(approved) not in json.dumps(result)


def test_textless_page_requires_ocr_and_fails_closed_for_quote_validation(tmp_path):
    approved = tmp_path / "approved"
    approved.mkdir()
    source = approved / "mixed.pdf"
    write_text_pdf(
        source,
        ["Produkt: okno\nSzerokość: 1200 mm\nWysokość: 1500 mm", ""],
    )

    result = legacy_pdf.analyze_pdf(source, allowed_roots=(approved,))

    assert result["ok"] is True
    assert result["status"] == "ocr_required"
    assert result["quote_facts"]["ocr_required_pages"] == [2]
    assert result["validation"]["can_execute"] is False
    assert any(
        conflict["code"] == "unverified_source_provenance"
        for conflict in result["validation"]["conflicts"]
    )


def test_analyze_pdf_rejects_paths_outside_approved_roots_without_disclosing_path(tmp_path):
    approved = tmp_path / "approved"
    approved.mkdir()
    outside = tmp_path / "outside.pdf"
    write_text_pdf(outside, ["Produkt: okno"])

    with pytest.raises(PdfDocumentError) as raised:
        legacy_pdf.analyze_pdf(outside, allowed_roots=(approved,))

    assert raised.value.code == "path_outside_allowed_roots"
    assert str(tmp_path) not in json.dumps(raised.value.to_payload())


@pytest.mark.parametrize(
    ("filename", "data", "expected_code"),
    [
        ("notes.txt", b"not a pdf", "unsupported_file_type"),
        ("broken.pdf", b"not a valid pdf", "invalid_pdf"),
    ],
)
def test_analyze_pdf_rejects_unsupported_and_malformed_files(
    tmp_path, filename, data, expected_code
):
    approved = tmp_path / "approved"
    approved.mkdir()
    source = approved / filename
    source.write_bytes(data)

    with pytest.raises(PdfDocumentError) as raised:
        legacy_pdf.analyze_pdf(source, allowed_roots=(approved,))

    assert raised.value.code == expected_code


def test_cli_writes_only_an_explicit_new_json_output_and_never_overwrites_source(tmp_path):
    approved = tmp_path / "approved"
    approved.mkdir()
    source = approved / "offer.pdf"
    original = write_text_pdf(
        source,
        ["Produkt: okno\nSzerokość: 1200 mm\nWysokość: 1500 mm"],
    )
    output = approved / "explicit-result.json"

    exit_code = legacy_pdf.main([
        "--source", str(source),
        "--allowed-root", str(approved),
        "--source-alias", "offer-alias",
        "--output", str(output),
    ])

    # The CLI writes a JSON result to stdout; this test checks the explicit file
    # separately via JSON and verifies that the source was left untouched.
    assert exit_code == 0
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["source"]["alias"] == "offer-alias"
    assert saved["validation"]["can_execute"] is True
    assert source.read_bytes() == original

    with pytest.raises(PdfDocumentError) as same_path:
        legacy_pdf._write_explicit_output(
            {"ok": True},
            output_path=source,
            source_path=source,
            allowed_roots=(approved,),
        )
    assert same_path.value.code == "source_overwrite_blocked"

    with pytest.raises(FileExistsError):
        legacy_pdf._write_explicit_output(
            {"ok": True},
            output_path=output,
            source_path=source,
            allowed_roots=(approved,),
        )
    assert source.read_bytes() == original


def test_explicit_output_path_must_be_approved_json_and_never_written_by_default(tmp_path, monkeypatch):
    approved = tmp_path / "approved"
    approved.mkdir()
    source = approved / "offer.pdf"
    write_text_pdf(source, ["Produkt: okno"])
    outside = tmp_path / "outside.json"

    with pytest.raises(PermissionError):
        legacy_pdf._write_explicit_output(
            {"ok": True},
            output_path=outside,
            source_path=source,
            allowed_roots=(approved,),
        )

    with pytest.raises(PdfDocumentError) as bad_type:
        legacy_pdf._write_explicit_output(
            {"ok": True},
            output_path=approved / "result.xlsx",
            source_path=source,
            allowed_roots=(approved,),
        )
    assert bad_type.value.code == "invalid_output_type"

    monkeypatch.chdir(approved)
    result = legacy_pdf.analyze_pdf(source, allowed_roots=(approved,))
    assert result["ok"] is True
    assert {path.name for path in approved.iterdir()} == {"offer.pdf"}
