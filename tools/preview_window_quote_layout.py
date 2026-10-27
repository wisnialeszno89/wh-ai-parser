"""Read-only local layout preview for window quote drawings and scanned pages."""
from __future__ import annotations

import argparse
from pathlib import Path

from app.agent.adapters.pdf_document_adapter import PdfDocumentAdapter, PdfDocumentError
from app.agent.offers.window_quote_layout import preview_window_quote_layout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preview per-position dimension candidates from a local PDF/photo. "
            "This is diagnostic only: no remote requests and no WindowHub actions."
        )
    )
    parser.add_argument("--source", required=True, help="PDF or image file to inspect.")
    parser.add_argument(
        "--approved-root",
        required=True,
        help="Directory explicitly approved as the source-file root.",
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

    print("mode: LOCAL_WINDOW_QUOTE_LAYOUT_PREVIEW_ONLY")
    print("remote_requests: 0")
    print("windowhub_actions: 0")
    print(f"source_type: {extraction.source_type}")
    print(f"page_count: {extraction.page_count}")

    all_candidates = []
    for page in extraction.pages:
        print()
        print(f"=== PAGE {page.page_number} ===")
        if page.needs_ocr:
            print("result: MANUAL_REVIEW_REQUIRED")
            print("reason: page_ocr_incomplete")
            print("position_count: 0")
            continue
        preview = preview_window_quote_layout(page.ocr_regions)
        payload = preview.to_payload()
        all_candidates.extend(
            (page.page_number, item) for item in preview.positions
        )
        print(f"position_count: {payload['position_count']}")
        print(f"complete_position_count: {payload['complete_position_count']}")
        print(f"total_quantity_candidate: {payload['total_quantity_candidate']}")
        print("manual_review_required: True")
        print("automatically_executable: False")
        for item in preview.positions:
            width = item.width_mm if item.width_mm is not None else "UNKNOWN"
            height = item.height_mm if item.height_mm is not None else "UNKNOWN"
            quantity = item.quantity if item.quantity is not None else "UNKNOWN"
            print(
                f"position={item.position_number} "
                f"width_mm_candidate={width} "
                f"height_mm_candidate={height} "
                f"quantity_candidate={quantity} "
                f"width_candidates={list(item.width_candidates_mm)} "
                f"height_candidates={list(item.height_candidates_mm)} "
                f"ocr_confidence_min={item.ocr_confidence_min}"
            )
            for limitation in item.limitations:
                print(f"  review_note: {limitation}")
        for limitation in preview.limitations:
            print(f"limitation: {limitation}")

    print()
    print(f"candidate_position_count: {len(all_candidates)}")
    print("manual_review_required: True")
    print("offer_created: False")
    print("result: LAYOUT_PREVIEW_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
