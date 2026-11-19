"""Dimension reconciliation using a verified manufacturer mounting convention.

Pure calculation only; no catalogue scraping or GUI write. An installation's
rules, box height and final readback must be verified independently.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HeightConvention(str, Enum):
    INCLUDED_IN_TOTAL = "box_included_in_total"
    ADDED_ABOVE_WINDOW = "box_added_above_window"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AssemblyDimensions:
    requested_width_mm: int
    requested_total_height_mm: int
    verified_box_height_mm: int | None
    convention: HeightConvention
    convention_verified: bool = False
    minimum_window_height_mm: int | None = None
    maximum_window_height_mm: int | None = None


@dataclass(frozen=True)
class DimensionResolution:
    status: str
    window_width_mm: int | None
    window_height_mm: int | None
    combined_height_mm: int | None
    reason: str


def reconcile_assembly(spec: AssemblyDimensions) -> DimensionResolution:
    """Preserve requested assembly envelope; fail closed on uncertain geometry."""
    if any(type(x) is not int or x <= 0 for x in
           (spec.requested_width_mm, spec.requested_total_height_mm)):
        return DimensionResolution("blocked", None, None, None, "invalid_requested_dimensions")
    if spec.convention == HeightConvention.UNKNOWN or not spec.convention_verified:
        return DimensionResolution("requires_catalogue_evidence", None, None, None,
                                   "mounting_convention_not_verified")
    box = spec.verified_box_height_mm
    if type(box) is not int or box <= 0:
        return DimensionResolution("requires_catalogue_evidence", None, None, None,
                                   "box_height_not_verified")
    if spec.convention == HeightConvention.INCLUDED_IN_TOTAL:
        window_height = spec.requested_total_height_mm - box
    elif spec.convention == HeightConvention.ADDED_ABOVE_WINDOW:
        # Here the manufacturer's window input refers to the bare window;
        # the assembly envelope still includes the box.
        window_height = spec.requested_total_height_mm - box
    else:
        return DimensionResolution("requires_catalogue_evidence", None, None, None,
                                   "unsupported_mounting_convention")
    if window_height <= 0:
        return DimensionResolution("blocked", None, None, None, "box_exceeds_total_height")
    if (spec.minimum_window_height_mm is not None
            and window_height < spec.minimum_window_height_mm):
        return DimensionResolution("blocked", None, None, None, "below_verified_product_minimum")
    if (spec.maximum_window_height_mm is not None
            and window_height > spec.maximum_window_height_mm):
        return DimensionResolution("blocked", None, None, None, "above_verified_product_maximum")
    return DimensionResolution("planned_requires_live_readback", spec.requested_width_mm,
                               window_height, window_height + box,
                               "verify_application_field_semantics_and_calculated_geometry")


def reconcile_window_and_box(
    *, window_height_mm: int, box_height_mm: int | None,
    box_height_verified: bool, requested_total_height_mm: int | None = None,
) -> DimensionResolution:
    """For enquiries specifying the bare window, do NOT shrink it.

    User input often specifies window height only and asks for a separate box.
    Total height is then the sum, once the box has been verified.
    """
    if type(window_height_mm) is not int or window_height_mm <= 0:
        return DimensionResolution("blocked", None, None, None, "invalid_window_height")
    if not box_height_verified or type(box_height_mm) is not int or box_height_mm <= 0:
        return DimensionResolution("requires_catalogue_evidence", None, window_height_mm,
                                   None, "box_height_not_verified")
    total = window_height_mm + box_height_mm
    if requested_total_height_mm is not None and total != requested_total_height_mm:
        return DimensionResolution("blocked", None, window_height_mm, total,
                                   "total_envelope_conflicts_with_requested_height")
    return DimensionResolution("planned_requires_live_readback", None, window_height_mm,
                               total, "verify_roller_total_dimension_in_target_field")
