"""Bounded local text/PDF intake for a single goal-driven agent request.

Extracts source text only; does not invent missing window parameters.
Scanned/photographic files require a separate vision/OCR pipeline.
"""
from __future__ import annotations

from pathlib import Path


def read_task_document(path: Path, *, max_file_bytes: int = 12_000_000, max_chars: int = 12_000) -> str:
    if not isinstance(path, Path):
        raise TypeError("task_document_path_required")
    if not path.is_file() or path.stat().st_size > max_file_bytes:
        raise ValueError("task_document_missing_or_too_large")
    suffix = path.suffix.casefold()
    if suffix in {".txt", ".md"}:
        content = path.read_text(encoding="utf-8-sig")
    elif suffix == ".pdf":
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for PDF task extraction") from exc
        with fitz.open(path) as document:
            if document.page_count > 40:
                raise ValueError("pdf_page_limit_exceeded")
            content = "\n".join(page.get_text("text") for page in document)
        if not content.strip():
            raise ValueError("scanned_pdf_requires_vision_ocr")
    else:
        raise ValueError("task_file_type_not_supported_use_text_or_pdf")
    content = content.strip()
    if not content:
        raise ValueError("task_document_empty")
    return content[:max_chars]
