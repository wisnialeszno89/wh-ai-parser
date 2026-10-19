from app.runtime.execution.vision.analyzers.hough_line_normalizer import (
    normalize_hough_line_segments,
)


class ArrayLike:
    def __init__(self, value):
        self.value = value

    def tolist(self):
        return self.value


EXPECTED = (
    (10, 20, 30, 40),
    (50, 60, 70, 80),
)


def test_normalizes_n_by_four_line_segments():
    assert normalize_hough_line_segments([
        [10, 20, 30, 40],
        [50, 60, 70, 80],
    ]) == EXPECTED


def test_normalizes_n_by_one_by_four_line_segments():
    assert normalize_hough_line_segments([
        [[10, 20, 30, 40]],
        [[50, 60, 70, 80]],
    ]) == EXPECTED


def test_normalizes_single_flat_segment():
    assert normalize_hough_line_segments([10, 20, 30, 40]) == (
        (10, 20, 30, 40),
    )


def test_accepts_numpy_style_tolist_objects():
    assert normalize_hough_line_segments(
        ArrayLike([[[10, 20, 30, 40]], [[50, 60, 70, 80]]])
    ) == EXPECTED


def test_empty_or_malformed_line_data_is_ignored():
    assert normalize_hough_line_segments(None) == ()
    assert normalize_hough_line_segments([]) == ()
    assert normalize_hough_line_segments([7]) == ()
