"""Conservative construction topology hints from the existing visual observer.

Only make suggestions for a verified WindowHub-owned pixel. Detected lines
can be edges of frame/sash or artwork; no component identity is proven.
"""
from __future__ import annotations


def visual_structure_hints(structure, ownership_status: str) -> dict[str, object]:
    if ownership_status != "owned_pixel_not_component_verified":
        return {
            "status": "blocked_unverified_window_owner",
            "vertical_internal_candidates": (),
            "horizontal_internal_candidates": (),
            "cell_candidates": 0,
            "components_verified": 0,
        }
    rect = getattr(structure, "construction_rect", None)
    if not isinstance(rect, tuple) or len(rect) != 4 or rect[2] <= 0 or rect[3] <= 0:
        return {
            "status": "blocked_missing_geometry",
            "vertical_internal_candidates": (),
            "horizontal_internal_candidates": (),
            "cell_candidates": 0,
            "components_verified": 0,
        }
    _x, _y, width, height = rect

    def internal(lines, dimension):
        lo, hi = 0.12 * dimension, 0.88 * dimension
        values = []
        for line in lines:
            at = getattr(line, "coordinate", None)
            strength = getattr(line, "strength", None)
            if (type(at) is int and type(strength) in (float, int)
                    and lo < at < hi and strength >= 0.11):
                values.append((at, round(float(strength), 3)))
        return tuple(sorted(values)[:12])

    return {
        "status": "geometry_hints_only",
        "vertical_internal_candidates": internal(getattr(structure, "vertical_lines", ()), width),
        "horizontal_internal_candidates": internal(getattr(structure, "horizontal_lines", ()), height),
        "cell_candidates": len(getattr(structure, "cells", ())),
        "components_verified": 0,
    }
