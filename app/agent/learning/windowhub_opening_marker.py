"""Read the lateral apex of the tilt-and-turn drawing in a single-sash WH crop."""

from typing import Literal

import numpy as np

MarkerSide = Literal["LEFT", "RIGHT"]


def read_opening_marker_side(rgb: np.ndarray) -> MarkerSide | None:
    """Read a WH drawing marker in the calibrated cyan-glass view."""
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected an RGB crop of one sash.")
    red, green, blue = np.moveaxis(rgb, -1, 0)
    glass = (red < 40) & (green > 175) & (green < 245) & (blue > 240)
    ys, xs = np.nonzero(glass)
    if not len(xs):
        return None
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    width, height = x1 - x0, y1 - y0
    if min(width, height) < 40 or glass[y0:y1 + 1, x0:x1 + 1].mean() < 0.7:
        return None

    # The native WH lines are dashed. Sample the interior of each ray in a
    # narrow band to tolerate gaps, rasterization and labels over the glass.
    dark = rgb.max(axis=-1) < 75
    samples = np.linspace(0.14, 0.86, 75)
    tolerance = max(2, round(height * 0.015))

    def coverage(ax, ay, bx, by):
        columns = np.rint(x0 + width * (ax + samples * (bx - ax))).astype(int)
        rows = np.rint(y0 + height * (ay + samples * (by - ay))).astype(int)
        bands = np.clip(rows + np.arange(-tolerance, tolerance + 1)[:, None], y0, y1)
        return float(dark[bands, columns].any(axis=0).mean())

    tilt = min(coverage(0.5, 0, 0, 1), coverage(0.5, 0, 1, 1))
    left = min(coverage(1, 0, 0, 0.5), coverage(1, 1, 0, 0.5))
    right = min(coverage(0, 0, 1, 0.5), coverage(0, 1, 1, 0.5))
    if tilt < 0.45 or max(left, right) < 0.45 or abs(left - right) < 0.2:
        return None
    return "LEFT" if left > right else "RIGHT"
