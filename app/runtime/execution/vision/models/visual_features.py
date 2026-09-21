from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VisualFeatures:
    """
    Low-level visual statistics extracted from a vision candidate.

    These features intentionally describe only visual density and do not
    assign any semantic UI meaning.
    """

    edge_density: float
    border_edge_density: float
    horizontal_edge_density: float
    vertical_edge_density: float
    contour_density: float
    dark_pixel_ratio: float
    bright_pixel_ratio: float
    interior_content_density: float
