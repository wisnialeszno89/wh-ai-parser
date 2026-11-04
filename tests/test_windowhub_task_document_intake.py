from pathlib import Path
import pytest

from app.agent.intake.task_document import read_task_document
from tools.run_windowhub_goal_v2 import parse_args


def test_text_task_file_is_usable_for_agent_goal(tmp_path):
    sample = tmp_path / "zapytanie.txt"
    sample.write_text("Jedno okno 1230x1478 antracyt jednostronny", encoding="utf-8")
    assert "1230x1478" in read_task_document(sample)
    parsed = parse_args(["--task-file", str(sample), "--mode", "inspect"])
    assert parsed.goal is None
    assert parsed.task_file == sample


def test_unsupported_document_formats_are_explicit(tmp_path):
    sample = tmp_path / "photo.png"
    sample.write_bytes(b"not_a_real_photo")
    with pytest.raises(ValueError, match="not_supported"):
        read_task_document(sample)


def test_pdf_text_is_extracted_when_pymupdf_available(tmp_path):
    fitz = pytest.importorskip("fitz")
    sample = tmp_path / "oferta.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((40, 50), "Window request 1230x1478")
    document.save(sample)
    document.close()
    assert "1230x1478" in read_task_document(sample)


def test_empty_scanned_pdf_fails_with_clear_reason(tmp_path):
    fitz = pytest.importorskip("fitz")
    sample = tmp_path / "scan.pdf"
    document = fitz.open()
    document.new_page()
    document.save(sample)
    document.close()
    with pytest.raises(ValueError, match="vision_ocr"):
        read_task_document(sample)
