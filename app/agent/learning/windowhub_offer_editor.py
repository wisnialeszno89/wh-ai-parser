"""Recognize the drawing and selected position in WindowHub's offer workspace."""
from __future__ import annotations

from dataclasses import dataclass
import re

import cv2
import numpy as np


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def center(self):
        return self.x + self.width // 2, self.y + self.height // 2

    def crop(self, image):
        return image[self.y:self.bottom, self.x:self.right]


def _boxes(mask):
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [Box(*cv2.boundingRect(contour)) for contour in contours]


def selected_row_box(rgb):
    """Join the selected blue cells across the one-pixel grid separators."""
    red, green, blue = np.moveaxis(rgb, -1, 0)
    selected = (red < 50) & (green >= 65) & (green <= 175) & (blue >= 165)
    rows = cv2.morphologyEx(selected.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((1, 11), np.uint8))
    candidates = [
        box for box in _boxes(rows)
        if box.width >= rgb.shape[1] * 0.35 and 12 <= box.height <= 70
        and box.y < rgb.shape[0] * 0.65
    ]
    return candidates[0] if len(candidates) == 1 else None


def selected_window_matches(lines, number, width, height):
    """Require ordinal, quantity, article, and exact dimensions in the selected row."""
    tokens = " ".join(
        line.label.casefold() for line in sorted(lines or (), key=lambda line: line.bounds[0])
        if line.confidence >= 0.80
    )
    return bool(
        re.match(rf"^{number}\s+1\s*okno(?:\s|$)", tokens)
        and re.search(rf"(?<!\d){width}\s*[x×]\s*{height}(?!\d)", tokens)
    )


def position_grid_bottom(dark, row):
    """Find the position table's lower edge connected to its left border."""
    left = max(0, row.x - 3)
    right = min(dark.shape[1], row.x + 2)
    region = dark[row.bottom:, row.x:row.right]
    for offset in np.flatnonzero(region.mean(axis=1) >= 0.90)[::-1]:
        if offset < 4:
            continue
        y = row.bottom + int(offset)
        # A toolbar or drawing line alone cannot be the grid bottom.
        if dark[row.bottom:y, left:right].mean(axis=0).max() >= 0.90:
            return y
    return None


def find_drawing(rgb, row):
    """Locate one rectangular drawing below the recognized position list."""
    red, green, blue = np.moveaxis(rgb, -1, 0)
    white = (red > 249) & (green > 249) & (blue > 249)
    frame = (red < 40) & (green < 60) & (blue > 240)
    dark = rgb.max(axis=2) < 90
    candidates = []
    height, width = rgb.shape[:2]
    grid_bottom = position_grid_bottom(dark, row)
    top = grid_bottom if grid_bottom is not None else row.bottom
    gap = max(85, round(height * 0.10)) if grid_bottom is not None else max(180, round(height * 0.22))
    for box in _boxes(white | frame):
        x, y, w, h = box.x, box.y, box.width, box.height
        if not (
            min(w, h) >= 85 and 0.55 <= w / h <= 1.65
            and 2 <= x < row.x + min(240, row.width // 4)
            and box.right < width and box.bottom < height
            and top + 4 < y <= top + gap
        ):
            continue
        # An empty drawing has a black perimeter; a built frame has a
        # continuous outer blue ring. Other white panes are ignored.
        if box.crop(frame).mean() >= 0.055:
            candidates.append(box)
        elif box.crop(white).mean() >= 0.97 and min(
            dark[y - 2:y, x:box.right].any(axis=0).mean(),
            dark[box.bottom:box.bottom + 2, x:box.right].any(axis=0).mean(),
            dark[y:box.bottom, x - 2:x].any(axis=1).mean(),
            dark[y:box.bottom, box.right:box.right + 2].any(axis=1).mean(),
        ) >= 0.87:
            candidates.append(box)
    # White interior islands share the same centre as the blue frame.
    outer = [b for b in candidates if not any(
        c != b and c.x <= b.x and c.y <= b.y and c.right >= b.right and c.bottom >= b.bottom
        for c in candidates
    )]
    return outer[0] if len(outer) == 1 else None


def fixed_window_stage(rgb):
    """Classify the small FIX build from component colors and glass topology."""
    from app.agent.learning.windowhub_opening_marker import read_opening_marker_side

    red, green, blue = np.moveaxis(rgb, -1, 0)
    frame = (red < 40) & (green < 60) & (blue > 240)
    inner_profile = (red < 40) & (green > 245) & (blue < 40)
    glass = (red < 40) & (green > 175) & (green < 245) & (blue > 240)
    white = (rgb > 249).all(axis=2)
    if white.mean() > 0.97:
        return "empty"
    # A sash adds a second profile band to the frame. The archived
    # single-sash examples have much more green than the frame alone.
    if not 0.065 <= frame.mean() <= 0.38 or inner_profile.mean() >= 0.16:
        return "unknown"
    if glass.mean() < 0.015 and white.mean() > 0.35:
        return "frame"
    regions = [box for box in _boxes(glass) if box.width * box.height >= glass.size * 0.08]
    if len(regions) == 1:
        pane = regions[0]
        if (
            glass.mean() > 0.35 and pane.crop(glass).mean() > 0.85
            and abs(pane.center[0] - rgb.shape[1] // 2) < rgb.shape[1] * 0.10
            and abs(pane.center[1] - rgb.shape[0] // 2) < rgb.shape[0] * 0.10
            and read_opening_marker_side(rgb) is None
        ):
            return "fixed_glazed"
    return "unknown"


def toolbar_tool(gray, template):
    """Find an unambiguous local match on the observed native toolbar."""
    matches = []
    for scale in (0.80, 0.90, 1.0, 1.1, 1.25, 1.5):
        height, width = (round(n * scale) for n in template.shape)
        if min(width, height) < 4 or height > gray.shape[0] or width > gray.shape[1]:
            continue
        resized = cv2.resize(template, (width, height), interpolation=cv2.INTER_LINEAR)
        scores = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        for _ in range(2):
            _, score, _, (x, y) = cv2.minMaxLoc(scores)
            matches.append((score, x + width // 2, y + height // 2))
            scores[max(0, y - height):y + height + 1, :] = -1
    if not matches:
        return None
    score, x, y = max(matches)
    rival = max((other for other, a, b in matches if abs(b - y) >= 12), default=-1)
    return (x, y) if score >= 0.82 and score - rival >= 0.045 else None
