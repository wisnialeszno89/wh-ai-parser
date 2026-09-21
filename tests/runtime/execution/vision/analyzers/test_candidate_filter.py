import cv2
import numpy as np

from app.runtime.execution.vision.analyzers.candidate_filter import (
    CandidateFilter,
)


def contour(x, y, width, height):
    return np.array(
        [
            [
                [x, y],
                [x + width, y],
                [x + width, y + height],
                [x, y + height],
            ]
        ],
        dtype=np.int32,
    )


def test_rejects_too_small_candidate():
    candidate_filter = CandidateFilter()

    result = candidate_filter.filter(
        [
            contour(
                10,
                10,
                8,
                8,
            )
        ],
        roi_width=1000,
        roi_height=1000,
    )

    assert result == []


def test_rejects_huge_container():
    candidate_filter = CandidateFilter()

    result = candidate_filter.filter(
        [
            contour(
                0,
                0,
                900,
                900,
            )
        ],
        roi_width=1000,
        roi_height=1000,
    )

    assert result == []


def test_keeps_normal_candidate():
    candidate_filter = CandidateFilter()

    result = candidate_filter.filter(
        [
            contour(
                100,
                100,
                100,
                40,
            )
        ],
        roi_width=1000,
        roi_height=1000,
    )

    assert len(result) == 1

    assert result[0].rect.x == 100
    assert result[0].rect.y == 100
    assert result[0].rect.width == 101
    assert result[0].rect.height == 41


def test_rejects_multi_border_container():
    candidate_filter = CandidateFilter()

    result = candidate_filter.filter(
        [
            contour(
                0,
                0,
                500,
                500,
            )
        ],
        roi_width=1000,
        roi_height=1000,
    )

    assert result == []


def test_rejects_extreme_aspect_ratio():
    candidate_filter = CandidateFilter()

    result = candidate_filter.filter(
        [
            contour(
                100,
                100,
                500,
                12,
            )
        ],
        roi_width=1000,
        roi_height=1000,
    )

    assert result == []


def test_deduplicates_overlapping_candidates():
    candidate_filter = CandidateFilter()

    result = candidate_filter.filter(
        [
            contour(
                100,
                100,
                100,
                40,
            ),
            contour(
                101,
                101,
                100,
                40,
            ),
        ],
        roi_width=1000,
        roi_height=1000,
    )

    assert len(result) == 1


def test_preserves_contour_hierarchy():
    candidate_filter = CandidateFilter()

    contours = [
        cv2.convexHull(
            __import__("numpy").array(
                [[[50, 50]], [[190, 50]], [[190, 190]], [[50, 190]]],
                dtype="int32",
            )
        ),
        cv2.convexHull(
            __import__("numpy").array(
                [[[80, 80]], [[160, 80]], [[160, 160]], [[80, 160]]],
                dtype="int32",
            )
        ),
    ]

    hierarchy = __import__("numpy").array(
        [[
            [-1, -1, 1, -1],
            [-1, -1, -1, 0],
        ]],
        dtype="int32",
    )

    result = candidate_filter.filter(
        contours,
        hierarchy=hierarchy,
        roi_width=300,
        roi_height=300,
    )

    assert len(result) == 2

    root = next(
        candidate
        for candidate in result
        if candidate.contour_index == 0
    )

    child = next(
        candidate
        for candidate in result
        if candidate.contour_index == 1
    )

    assert root.parent_contour_index is None
    assert root.depth == 0
    assert root.is_root is True

    assert child.parent_contour_index == 0
    assert child.depth == 1
    assert child.is_root is False

def test_relinks_child_to_surviving_ancestor_after_duplicate_parent_is_removed():
    candidate_filter = CandidateFilter()

    contours = [
        contour(100, 100, 100, 40),
        contour(100, 100, 100, 40),
        contour(120, 110, 40, 20),
    ]

    hierarchy = np.array(
        [[
            [-1, -1, -1, -1],
            [-1, -1, 2, -1],
            [-1, -1, -1, 1],
        ]],
        dtype=np.int32,
    )

    result = candidate_filter.filter(
        contours,
        hierarchy=hierarchy,
        roi_width=1000,
        roi_height=1000,
    )

    assert len(result) == 2

    root = next(
        candidate
        for candidate in result
        if candidate.contour_index == 0
    )

    child = next(
        candidate
        for candidate in result
        if candidate.contour_index == 2
    )

    assert root.parent_contour_index is None
    assert root.depth == 0
    assert root.is_root is True

    assert child.parent_contour_index == 0
    assert child.depth == 1
    assert child.is_root is False
