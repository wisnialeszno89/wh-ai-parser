"""Read-only construction planning for the archived WindowHub single-sash view."""

from dataclasses import dataclass

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from app.agent.learning.windowhub_opening_marker import read_opening_marker_side
from app.gui.enums.gui_tool import GuiTool

NEXT_STEP = {
    "empty": (GuiTool.FRAME, "frame"),
    "frame": (GuiTool.SASH, "sash"),
    "sash": (GuiTool.GLASS, "glass"),
    "glass": (GuiTool.HARDWARE, "opening_marker"),
}


def read_builder_stage(rgb: np.ndarray) -> str:
    """Classify a canvas crop using the archived editor's rendering palette."""
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected an RGB construction crop.")
    red, green, blue = np.moveaxis(rgb, -1, 0)
    white = ((red > 250) & (green > 250) & (blue > 250)).mean()
    frame = ((red < 40) & (green < 60) & (blue > 240)).mean()
    sash = ((red < 40) & (green > 245) & (blue < 40)).mean()
    glass = ((red < 40) & (green > 175) & (green < 245) & (blue > 240)).mean()

    if frame < 0.02 and sash < 0.02 and glass < 0.02 and white > 0.65:
        return "empty"
    if frame < 0.07:
        return "unknown"
    if glass > 0.30 and sash > 0.15:
        return "opening_marker" if read_opening_marker_side(rgb) else "glass"
    if glass < 0.02:
        if 0.04 <= sash < 0.13:
            return "frame"
        if sash > 0.20:
            return "sash"
    return "unknown"


def read_builder_geometry(rgb: np.ndarray) -> str:
    """Classify a drawing from its four profile bands and its center."""
    red, green, blue = np.moveaxis(rgb, -1, 0)
    outer = (red < 40) & (green < 60) & (blue > 220)
    inner = (red < 45) & (green > 205) & (blue < 55)
    pane = (red < 45) & (green > 175) & (green < 245) & (blue > 240)
    h, w = outer.shape
    rim = min(h, w) // 4
    if rim < 12:
        return "unknown"

    def sides(mask):
        middle_x = slice(w // 3, 2 * w // 3)
        middle_y = slice(h // 3, 2 * h // 3)
        return (
            mask[:rim, middle_x].mean(axis=1),
            mask[-rim:, middle_x].mean(axis=1)[::-1],
            mask[middle_y, :rim].mean(axis=0),
            mask[middle_y, -rim:].mean(axis=0)[::-1],
        )

    blue_bands = [np.flatnonzero(side >= 0.78) for side in sides(outer)]
    if any(len(band) < 2 for band in blue_bands):
        return "unknown"
    sash_sides = []
    for side, band in zip(sides(inner), blue_bands):
        green_band = side[band[-1] + 1:] >= 0.72
        sash_sides.append(bool((green_band[:-1] & green_band[1:]).any()))
    core = rgb[h // 3:2*h // 3, w // 3:2*w // 3]
    white_center = ((core > 245).all(axis=-1)).mean() >= 0.62
    if all(sash_sides):
        if pane[h // 3:2*h // 3, w // 3:2*w // 3].mean() > 0.68:
            return "opening_marker" if read_opening_marker_side(rgb) else "glass"
        if white_center and pane.mean() < 0.015:
            return "sash"
    if not any(sash_sides) and white_center and pane.mean() < 0.015:
        return "frame"
    return "unknown"


def observe_builder_stage(rgb: np.ndarray) -> str:
    stage = read_builder_stage(rgb)
    if stage == "unknown":
        stage = read_builder_geometry(rgb)
    return stage


@dataclass(frozen=True)
class ToolbarMatch:
    x: int
    y: int
    score: float


def match_archived_toolbar(toolbar: np.ndarray, template: np.ndarray) -> ToolbarMatch | None:
    """Match a grayscale template and reject similar candidates at other heights."""
    height, width = template.shape
    if height > toolbar.shape[0] or width > toolbar.shape[1]:
        return None
    template = template.astype(np.float32)
    template -= template.mean()
    windows = sliding_window_view(toolbar.astype(np.float32), template.shape).copy()
    windows -= windows.mean(axis=(-2, -1), keepdims=True)
    scores = (windows * template).sum(axis=(-2, -1)) / (
        np.linalg.norm(windows, axis=(-2, -1)) * np.linalg.norm(template) + 1e-6
    )
    y, x = np.unravel_index(scores.argmax(), scores.shape)
    best = float(scores[y, x])
    separation = max(1, height // 2)
    scores[max(0, y - separation):y + separation + 1, :] = -1
    if best < 0.82 or best - float(scores.max()) < 0.045:
        return None
    return ToolbarMatch(int(x + width // 2), int(y + height // 2), best)
