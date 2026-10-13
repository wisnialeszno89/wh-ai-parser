"""OCR-to-table reconstruction and model-safe payload for WindowHub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

import numpy as np

from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow, parse_windowhub_ocr_table
from app.agent.perception.windowhub_ocr_table_refiner import (
    WindowHubOCRFieldRefinement,
    refine_windowhub_ocr_table_lp,
    refine_windowhub_ocr_table_rows,
)


@dataclass(frozen=True)
class WindowHubOCRTableReconstruction:
    rows: tuple[WindowHubOCRTableRow, ...]
    field_refinements: tuple[WindowHubOCRFieldRefinement, ...]
    lp_refinements: tuple[WindowHubOCRFieldRefinement, ...]

    def to_payload(self) -> dict[str, object]:
        """Serialize table values and audit data without exposing coordinates."""
        complete_count = sum(row.complete for row in self.rows)
        status = "empty" if not self.rows else (
            "complete" if complete_count == len(self.rows) else "partial"
        )
        return {
            "source": "windowhub_ocr_table_reconstruction",
            "status": status,
            "row_count": len(self.rows),
            "complete_row_count": complete_count,
            "rows": [row.to_payload() for row in self.rows],
            "field_refinements": [item.to_payload() for item in self.field_refinements],
            "lp_refinements": [item.to_payload() for item in self.lp_refinements],
            "limitations": [
                "Values are OCR-derived observations, not independently verified document facts.",
                "Do not perform consequential actions solely because OCR reported a complete row.",
            ],
        }


def reconstruct_windowhub_ocr_table_rows(
    ocr_elements: Any,
    screenshot_or_image: Any,
    engine: Callable[[np.ndarray], Any],
    *,
    parser_options: Mapping[str, Any] | None = None,
    field_refiner_options: Mapping[str, Any] | None = None,
    lp_refiner_options: Mapping[str, Any] | None = None,
) -> WindowHubOCRTableReconstruction:
    """Parse rows anchored by prices, refine missing fields, then recover LP."""
    parser_kwargs = dict(parser_options or {})
    if "anchor_x_max" in parser_kwargs:
        raise ValueError(
            "parser_options must not override anchor_x_max; price-column anchors protect against partial LP OCR."
        )
    rows = parse_windowhub_ocr_table(ocr_elements, anchor_x_max=-1.0, **parser_kwargs)
    image = getattr(screenshot_or_image, "image", screenshot_or_image)
    image_array = np.asarray(image)
    refined_rows, field_reports = refine_windowhub_ocr_table_rows(
        rows, image_array, engine, **dict(field_refiner_options or {})
    )
    refined_rows, lp_reports = refine_windowhub_ocr_table_lp(
        refined_rows, image_array, engine, **dict(lp_refiner_options or {})
    )
    return WindowHubOCRTableReconstruction(
        rows=refined_rows,
        field_refinements=field_reports,
        lp_refinements=lp_reports,
    )
