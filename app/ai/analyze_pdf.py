"""Safe legacy CLI entry point for local PDF fact extraction.

This module is import-safe: importing it does not open files, import a model
provider, call a network, render PDF pages, or write outputs. The CLI defaults
to deterministic local text extraction and quote-fact validation only. Pages
without extractable text are reported as OCR-needed; no speculative vision or
price inference is performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from app.agent.adapters.pdf_document_adapter import (
    PdfDocumentAdapter,
    PdfDocumentError,
)
from app.agent.offers.pdf_quote_fact_extractor import PdfQuoteFactExtractor
from app.agent.offers.quote_facts import QuoteFactValidator


def analyze_pdf(
    source_path: str | Path,
    *,
    allowed_roots: Sequence[str | Path],
    source_alias: str | None = None,
) -> dict[str, object]:
    """Extract bounded local PDF text into provenance-aware quote facts.

    No model, OCR, output file, GUI or network is used. The returned payload
    contains only page metadata, explicitly labelled quote facts, evidence
    lines and deterministic validation. Raw unstructured page text stays out
    of the result unless an exact evidence line matched a supported fact.
    """
    adapter = PdfDocumentAdapter(allowed_roots=allowed_roots)
    extraction = adapter.extract(source_path, source_alias=source_alias)
    fact_extraction = PdfQuoteFactExtractor().extract(extraction)

    validation = QuoteFactValidator().validate(
        fact_extraction.facts,
        known_sources={extraction.source_alias: extraction},
    )

    status = (
        "ocr_required"
        if extraction.needs_ocr
        else "manual_review"
        if validation.requires_manual_review
        else "validated"
    )
    return {
        "ok": True,
        "status": status,
        "source": {
            "alias": extraction.source_alias,
            "file_size_bytes": extraction.file_size_bytes,
            "page_count": extraction.page_count,
            "extraction_status": extraction.status,
            "extracted_text_chars": extraction.extracted_text_chars,
            "pages": [
                {
                    "page_number": page.page_number,
                    "text_chars": len(page.text),
                    "extraction_method": page.extraction_method,
                    "needs_ocr": page.needs_ocr,
                    "limitations": list(page.limitations),
                }
                for page in extraction.pages
            ],
        },
        "quote_facts": fact_extraction.to_payload(),
        "validation": validation.to_payload(),
        "side_effects": {
            "model_calls": 0,
            "network_calls": 0,
            "gui_actions": 0,
            "source_files_modified": 0,
        },
    }


def _safe_error(exc: Exception) -> dict[str, object]:
    """Translate local failures without returning paths or provider details."""
    if isinstance(exc, PdfDocumentError):
        payload = exc.to_payload()
        payload["ok"] = False
        return payload
    if isinstance(exc, PermissionError):
        return {
            "ok": False,
            "error": {
                "code": "path_not_allowed",
                "message": "The source or output path is outside the configured allowed roots.",
            },
        }
    if isinstance(exc, FileExistsError):
        return {
            "ok": False,
            "error": {
                "code": "output_already_exists",
                "message": "The requested output already exists; it was not overwritten.",
            },
        }
    if isinstance(exc, (OSError, ValueError, TypeError)):
        return {
            "ok": False,
            "error": {
                "code": "invalid_input",
                "message": "The request could not be completed with the supplied local paths or parameters.",
            },
        }
    return {
        "ok": False,
        "error": {
            "code": "local_processing_failed",
            "message": "Local PDF processing failed. Details were withheld to avoid exposing machine paths or document contents.",
        },
    }


def _write_explicit_output(
    payload: dict[str, object],
    *,
    output_path: str | Path,
    source_path: str | Path,
    allowed_roots: Sequence[str | Path],
) -> Path:
    """Write JSON only to an explicit, approved, new .json path."""
    if not isinstance(output_path, (str, Path)) or not str(output_path).strip():
        raise ValueError("A non-empty output path is required.")

    roots = tuple(Path(root).expanduser().resolve() for root in allowed_roots)
    destination = Path(output_path).expanduser().resolve(strict=False)
    source = Path(source_path).expanduser().resolve(strict=True)

    if destination == source:
        raise PdfDocumentError(
            "source_overwrite_blocked",
            "The output path cannot be the source PDF.",
        )
    if destination.suffix.casefold() != ".json":
        raise PdfDocumentError(
            "invalid_output_type",
            "The explicit output path must use the .json extension.",
        )
    if not any(_under_root(destination, root) for root in roots):
        raise PermissionError("Output path is outside approved roots.")
    if destination.exists():
        raise FileExistsError(destination)
    if not destination.parent.is_dir():
        raise PdfDocumentError(
            "output_parent_missing",
            "The output parent directory must already exist.",
        )

    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    # Exclusive creation prevents a race from replacing an existing file.
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)
    return destination


def _under_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract explicitly labelled quote facts from a local PDF. "
            "No model/API key, OCR, GUI action or network access is used."
        )
    )
    parser.add_argument(
        "--source",
        required=True,
        help="PDF path within a folder explicitly approved by --allowed-root.",
    )
    parser.add_argument(
        "--allowed-root",
        action="append",
        required=True,
        help="Approved local root; may be supplied more than once.",
    )
    parser.add_argument(
        "--source-alias",
        default=None,
        help="Optional short provenance alias (defaults to the PDF filename).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Optional explicit new JSON output path inside an allowed root. "
            "Existing files and the source PDF are never overwritten. "
            "Without --output, JSON is printed only to stdout."
        ),
    )
    args = parser.parse_args(argv)

    try:
        payload = analyze_pdf(
            args.source,
            allowed_roots=args.allowed_root,
            source_alias=args.source_alias,
        )
        if args.output:
            _write_explicit_output(
                payload,
                output_path=args.output,
                source_path=args.source,
                allowed_roots=args.allowed_root,
            )
    except Exception as exc:
        payload = _safe_error(exc)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
