"""Read-only local OCR preview for a PDF or photo; never touches WindowHub."""
from __future__ import annotations

import argparse
from pathlib import Path

from app.agent.adapters.pdf_document_adapter import (
    PdfDocumentAdapter,
    PdfDocumentError,
)
from app.agent.offers.drawing_position_extractor import DrawingPositionExtractor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract readable text from a local PDF/photo and print OCR confidence. "
            "This tool makes no remote requests and performs no GUI actions."
        )
    )
    parser.add_argument("--source", required=True, help="PDF or image file to inspect.")
    parser.add_argument(
        "--approved-root",
        required=True,
        help="Directory explicitly approved as the source-file root.",
    )
    parser.add_argument(
        "--show-regions",
        action="store_true",
        help="Also print recognized text-box positions and confidence scores.",
    )
    parser.add_argument(
        "--show-drawing-positions",
        action="store_true",
        help="Print review-only candidates for window-drawing position, quantity, width and height.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        approved_root = Path(args.approved_root).expanduser().resolve(strict=True)
        if not approved_root.is_dir():
            print("result: ABORTED")
            print("reason: approved_root_not_directory")
            return 2

        adapter = PdfDocumentAdapter(allowed_roots=(approved_root,))
        extraction = adapter.extract(args.source, source_alias=Path(args.source).name)
    except PdfDocumentError as exc:
        print("result: ABORTED")
        print(f"reason: {exc.code}")
        print("source_path_printed: False")
        return 2
    except Exception as exc:
        print("result: ABORTED")
        print(f"error_type: {type(exc).__name__}")
        print("error_details_printed: False")
        print("source_path_printed: False")
        return 2

    print("mode: LOCAL_OCR_PREVIEW_ONLY")
    print("remote_requests: 0")
    print("windowhub_actions: 0")
    print(f"source_type: {extraction.source_type}")
    print(f"page_count: {extraction.page_count}")
    print(f"extraction_status: {extraction.status}")
    print(f"needs_ocr_or_manual_review: {extraction.needs_ocr}")

    for page in extraction.pages:
        print()
        print(f"=== PAGE {page.page_number} ===")
        print(f"extraction_method: {page.extraction_method}")
        print(f"needs_ocr: {page.needs_ocr}")
        if page.extraction_confidence is None:
            print("average_ocr_confidence: unavailable")
        else:
            print(f"average_ocr_confidence: {page.extraction_confidence:.3f}")
        print(f"ocr_region_count: {len(page.ocr_regions)}")
        print("recognized_text_begin")
        print(page.text if page.text else "(no readable text)")
        print("recognized_text_end")
        for limitation in page.limitations:
            print(f"limitation: {limitation}")
        if args.show_drawing_positions:
            drawing_result = DrawingPositionExtractor().extract(page)
            print("drawing_positions_begin")
            for candidate in drawing_result.positions:
                confidence = (
                    "unavailable"
                    if candidate.confidence is None
                    else f"{candidate.confidence:.3f}"
                )
                print(
                    f"position={candidate.position_number} "
                    f"quantity={candidate.quantity if candidate.quantity is not None else 'MISSING'} "
                    f"width_mm={candidate.width_mm if candidate.width_mm is not None else 'MISSING'} "
                    f"height_mm={candidate.height_mm if candidate.height_mm is not None else 'MISSING'} "
                    f"confidence={confidence} "
                    f"complete={candidate.complete}"
                )
                print(
                    f"  evidence: quantity={candidate.quantity_evidence!r}; "
                    f"width={candidate.width_evidence!r}; "
                    f"height={candidate.height_evidence!r}"
                )
                for issue in candidate.issues:
                    print(f"  position_issue: {issue}")
            for issue in drawing_result.issues:
                print(f"drawing_issue: {issue}")
            print("requires_visual_review: True")
            print("drawing_positions_end")

        if args.show_regions:
            print("ocr_regions_begin")
            for region in page.ocr_regions:
                confidence = (
                    "unavailable"
                    if region.confidence is None
                    else f"{region.confidence:.3f}"
                )
                print(
                    f"confidence={confidence} "
                    f"bounds={region.x},{region.y},{region.width},{region.height} "
                    f"text={region.text}"
                )
            print("ocr_regions_end")

    print()
    print(
        "result: REVIEW_REQUIRED"
        if extraction.needs_ocr
        else "result: OCR_TEXT_AVAILABLE_FOR_FIELD_VALIDATION"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
