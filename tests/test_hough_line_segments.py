"""Regression: OpenCV HoughLinesP output can be N x 4 or N x 1 x 4."""
import numpy as np
import pytest

from app.runtime.execution.vision.analyzers.hough_line_segments import (
    hough_line_segments,
)


@pytest.mark.parametrize("shape", [(2, 1, 4), (2, 4)])
def test_hough_line_segments_normalizes_both_opencv_layouts(shape):
    raw = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.int32).reshape(shape)
    assert hough_line_segments(raw) == ((1, 2, 3, 4), (5, 6, 7, 8))


def test_hough_line_segments_none_and_empty():
    assert hough_line_segments(None) == ()
    assert hough_line_segments(np.empty((0, 1, 4), dtype=np.int32)) == ()


@pytest.mark.parametrize("shape", [(4,), (2, 1, 1), (2, 2, 4)])
def test_hough_line_segments_rejects_malformed_shapes(shape):
    with pytest.raises(ValueError, match="unexpected_hough_lines_shape"):
        hough_line_segments(np.zeros(shape, dtype=np.int32))


def test_hough_line_segments_rejects_non_numeric_values():
    with pytest.raises(ValueError, match="unexpected_hough_lines_dtype"):
        hough_line_segments(np.full((1, 4), "x"))
