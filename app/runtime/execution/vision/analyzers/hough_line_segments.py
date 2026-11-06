"""Normalize OpenCV HoughLinesP outputs across OpenCV versions.

Accept both (N, 1, 4) and (N, 4) layouts. Reject malformed data
instead of interpreting one numpy scalar as a full line.
"""
from __future__ import annotations

import numpy as np


def hough_line_segments(lines) -> tuple[tuple[int, int, int, int], ...]:
    if lines is None:
        return ()
    array = np.asarray(lines)
    if array.size == 0:
        return ()
    if array.ndim not in (2, 3) or array.shape[-1] != 4:
        raise ValueError("unexpected_hough_lines_shape")
    if array.ndim == 3 and array.shape[1] != 1:
        raise ValueError("unexpected_hough_lines_shape")
    if not np.issubdtype(array.dtype, np.number):
        raise ValueError("unexpected_hough_lines_dtype")
    return tuple(tuple(int(value) for value in segment) for segment in array.reshape(-1, 4))
