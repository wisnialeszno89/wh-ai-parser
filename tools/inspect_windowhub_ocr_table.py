from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    """Run a read-only OCR/table observation on the already focused WindowHub."""
    if os.name != "nt":
        print("ABORTED: this diagnostic requires Windows.")
        return 2

    # Import Windows-specific repository modules only after the platform guard.
    from app.agent.environment.windowhub_environment_adapter import (
        WindowHubEnvironmentAdapter,
    )
    from app.agent.perception.windowhub_ocr_provider import WindowHubOCRProvider

    print("WindowHub OCR table inspection (READ ONLY)")
    print("==========================================")
    print("No focus changes, clicks, typing, or other GUI actions will be performed.")
    print()

    try:
        observation = WindowHubEnvironmentAdapter().observe()
    except Exception as exc:
        print(
            "ABORTED: could not capture WindowHub observation: "
            f"{type(exc).__name__}: {exc}"
        )
        return 3

    title = str(getattr(observation.state, "active_window_title", "") or "")
    focused = observation.metadata.get("window_focused") is True
    print(f"window_title={title!r}")
    print(f"window_focused={focused}")
    print(f"screenshot_source={observation.metadata.get('source')!r}")

    if not focused:
        print()
        print("ABORTED: WindowHub is not the foreground window.")
        print("Bring the intended WindowHub OFR table to the foreground and rerun.")
        print("This diagnostic will not activate or focus a window for you.")
        return 4

    if "OFR/" not in title.upper():
        print()
        print("ABORTED: the active WindowHub title does not identify an OFR/ offer.")
        print("Open the intended offer table, keep it in the foreground, and rerun.")
        return 5

    try:
        elements = WindowHubOCRProvider().perceive(observation)
    except Exception as exc:
        print(
            f"ABORTED: OCR provider failed unexpectedly: "
            f"{type(exc).__name__}: {exc}"
        )
        return 6

    metadata = observation.metadata
    reconstruction = metadata.get("windowhub_ocr_table_reconstruction")
    payload = reconstruction.to_payload() if reconstruction is not None else None

    summary = {
        "window_title": title,
        "window_focused": focused,
        "ocr_status": metadata.get("windowhub_ocr_status"),
        "ocr_element_count": metadata.get("windowhub_ocr_element_count", len(elements)),
        "table_status": metadata.get("windowhub_ocr_table_status", "not_available"),
        "table_error_type": metadata.get("windowhub_ocr_table_error"),
        "table_row_count": metadata.get("windowhub_ocr_table_row_count", 0),
        "table_complete_row_count": metadata.get(
            "windowhub_ocr_table_complete_row_count", 0
        ),
        "table_field_refinement_count": metadata.get(
            "windowhub_ocr_table_field_refinement_count", 0
        ),
        "table_lp_refinement_count": metadata.get(
            "windowhub_ocr_table_lp_refinement_count", 0
        ),
        "table": payload,
        "safety_note": (
            "OCR-derived values are observations, not independently verified facts. "
            "This diagnostic does not execute GUI actions."
        ),
    }

    print()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

    if summary["ocr_status"] == "error":
        return 9
    if summary["table_status"] == "error":
        return 7
    if summary["table_row_count"] <= 0:
        return 8
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
