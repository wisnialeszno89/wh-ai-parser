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
