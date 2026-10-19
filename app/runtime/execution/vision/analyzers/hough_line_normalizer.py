from __future__ import annotations

from typing import Any


def normalize_hough_line_segments(
    lines: Any,
) -> tuple[tuple[int, int, int, int], ...]:
    """Normalize OpenCV HoughLinesP output across common array shapes.

    OpenCV can expose line segments as (N, 1, 4), (N, 4), or a single
    four-value segment. The tolist method supports NumPy arrays without
    requiring NumPy in this independently testable normalizer.
    """
    if lines is None:
        return ()

    tolist = getattr(lines, "tolist", None)
    if callable(tolist):
        try:
            lines = tolist()
        except (TypeError, ValueError):
            return ()

    segments: list[tuple[int, int, int, int]] = []
    malformed = False

    def visit(value: Any) -> None:
        nonlocal malformed

        if not isinstance(value, (list, tuple)):
            malformed = True
            return

        if len(value) == 4 and all(
            not isinstance(item, (list, tuple))
            for item in value
        ):
            try:
                segments.append(tuple(int(item) for item in value))
            except (TypeError, ValueError, OverflowError):
                malformed = True
            return

        for child in value:
            visit(child)

    visit(lines)

    if malformed:
        return ()

    return tuple(segments)
