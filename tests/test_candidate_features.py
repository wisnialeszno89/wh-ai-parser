from app.runtime.execution.vision.analyzers.candidate_features import (
    CandidateFeatureExtractor,
)
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.vision_candidate import VisionCandidate


def candidate(
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    contour_index: int,
    parent: int | None = None,
    depth: int = 0,
) -> VisionCandidate:
    return VisionCandidate(
        rect=Rect(x, y, width, height),
        contour_index=contour_index,
        parent_contour_index=parent,
        depth=depth,
    )


def test_extracts_basic_geometry():
    candidates = [
        candidate(
            x=100,
            y=50,
            width=200,
            height=100,
            contour_index=0,
        )
    ]

    features = CandidateFeatureExtractor().extract(
        candidates,
        roi_width=1000,
        roi_height=500,
    )

    assert len(features) == 1

    feature = features[0]

    assert feature.width == 200
    assert feature.height == 100
    assert feature.area == 20_000

    assert feature.aspect_ratio == 2.0

    assert feature.area_ratio == 20_000 / 500_000
    assert feature.width_ratio == 0.2
    assert feature.height_ratio == 0.2

    assert feature.center_x == 0.2
    assert feature.center_y == 0.2


def test_detects_shape_helpers():
    candidates = [
        candidate(
            x=100,
            y=100,
            width=100,
            height=100,
            contour_index=0,
        ),
        candidate(
            x=250,
            y=100,
            width=300,
            height=100,
            contour_index=1,
        ),
        candidate(
            x=650,
            y=100,
            width=50,
            height=200,
            contour_index=2,
        ),
    ]

    features = CandidateFeatureExtractor().extract(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert features[0].is_square
    assert not features[0].is_wide
    assert not features[0].is_tall

    assert features[1].is_wide
    assert not features[1].is_square

    assert features[2].is_tall
    assert not features[2].is_square


def test_detects_roi_border_contacts():
    candidates = [
        candidate(
            x=0,
            y=10,
            width=100,
            height=50,
            contour_index=0,
        ),
        candidate(
            x=900,
            y=10,
            width=100,
            height=50,
            contour_index=1,
        ),
        candidate(
            x=10,
            y=0,
            width=100,
            height=50,
            contour_index=2,
        ),
        candidate(
            x=10,
            y=900,
            width=100,
            height=100,
            contour_index=3,
        ),
    ]

    features = CandidateFeatureExtractor().extract(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert features[0].touches_left
    assert not features[0].touches_right

    assert features[1].touches_right
    assert not features[1].touches_left

    assert features[2].touches_top
    assert not features[2].touches_bottom

    assert features[3].touches_bottom
    assert not features[3].touches_top


def test_sibling_count_uses_parent_relationship():
    candidates = [
        candidate(
            x=10,
            y=10,
            width=100,
            height=50,
            contour_index=0,
            parent=None,
        ),
        candidate(
            x=20,
            y=70,
            width=100,
            height=50,
            contour_index=1,
            parent=0,
            depth=1,
        ),
        candidate(
            x=130,
            y=70,
            width=100,
            height=50,
            contour_index=2,
            parent=0,
            depth=1,
        ),
        candidate(
            x=240,
            y=70,
            width=100,
            height=50,
            contour_index=3,
            parent=0,
            depth=1,
        ),
        candidate(
            x=20,
            y=140,
            width=50,
            height=30,
            contour_index=4,
            parent=1,
            depth=2,
        ),
    ]

    features = CandidateFeatureExtractor().extract(
        candidates,
        roi_width=500,
        roi_height=500,
    )

    assert features[0].sibling_count == 0

    assert features[1].sibling_count == 2
    assert features[2].sibling_count == 2
    assert features[3].sibling_count == 2

    assert features[4].sibling_count == 0


def test_preserves_depth():
    candidates = [
        candidate(
            x=10,
            y=10,
            width=100,
            height=100,
            contour_index=0,
            depth=0,
        ),
        candidate(
            x=20,
            y=20,
            width=50,
            height=50,
            contour_index=1,
            parent=0,
            depth=1,
        ),
        candidate(
            x=30,
            y=30,
            width=25,
            height=25,
            contour_index=2,
            parent=1,
            depth=2,
        ),
    ]

    features = CandidateFeatureExtractor().extract(
        candidates,
        roi_width=500,
        roi_height=500,
    )

    assert [feature.depth for feature in features] == [0, 1, 2]


def test_child_count_comes_from_candidate_hierarchy():
    parent = candidate(
        x=10,
        y=10,
        width=100,
        height=100,
        contour_index=10,
        depth=0,
    )

    child_a = candidate(
        x=20,
        y=20,
        width=30,
        height=30,
        contour_index=11,
        parent=10,
        depth=1,
    )

    child_b = candidate(
        x=60,
        y=20,
        width=30,
        height=30,
        contour_index=12,
        parent=10,
        depth=1,
    )

    features = CandidateFeatureExtractor().extract(
        [parent, child_a, child_b],
        roi_width=200,
        roi_height=200,
    )

    assert features[0].child_count == 2
    assert features[1].child_count == 0
    assert features[2].child_count == 0
