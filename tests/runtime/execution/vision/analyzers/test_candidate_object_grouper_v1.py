from app.runtime.execution.vision.analyzers.candidate_object_grouper_v1 import (
    CandidateObjectGrouperV1,
)
from app.runtime.execution.vision.analyzers.candidate_hierarchy import (
    CandidateNode,
)
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.vision_candidate import VisionCandidate


def candidate(
    index: int,
    rect: Rect,
    *,
    parent: int | None = None,
    depth: int = 0,
) -> VisionCandidate:
    return VisionCandidate(
        rect=rect,
        contour_index=index,
        parent_contour_index=parent,
        depth=depth,
    )


def node(candidate_: VisionCandidate, *children: CandidateNode) -> CandidateNode:
    return CandidateNode(
        candidate=candidate_,
        children=tuple(children),
    )


def test_groups_compound_object():
    root = candidate(
        745,
        Rect(47, 192, 56, 21),
    )
    child = candidate(
        747,
        Rect(49, 194, 52, 17),
        parent=745,
        depth=1,
    )

    hierarchy = (
        node(
            root,
            node(child),
        ),
    )

    objects = CandidateObjectGrouperV1().group(
        hierarchy,
        roi_width=1917,
        roi_height=1152,
    )

    assert len(objects) == 1

    logical = objects[0]

    assert logical.root_contour_index == 745
    assert logical.member_contour_indices == (745, 747)
    assert logical.member_count == 2
    assert logical.is_compound
    assert logical.bounds == Rect(47, 192, 56, 21)


def test_groups_multiple_direct_children():
    root = candidate(
        1100,
        Rect(655, 175, 165, 33),
    )
    child_a = candidate(
        1127,
        Rect(657, 177, 161, 29),
        parent=1100,
        depth=1,
    )
    child_b = candidate(
        1120,
        Rect(657, 205, 40, 2),
        parent=1100,
        depth=1,
    )

    hierarchy = (
        node(
            root,
            node(child_a),
            node(child_b),
        ),
    )

    objects = CandidateObjectGrouperV1().group(
        hierarchy,
        roi_width=1917,
        roi_height=1152,
    )

    assert len(objects) == 1
    assert objects[0].root_contour_index == 1100
    assert objects[0].member_contour_indices == (1100, 1127, 1120)


def test_does_not_group_large_container():
    root = candidate(
        1217,
        Rect(44, 172, 1358, 205),
    )

    children = tuple(
        node(
            candidate(
                2000 + index,
                Rect(100 + index * 20, 180, 20, 20),
                parent=1217,
                depth=1,
            )
        )
        for index in range(6)
    )

    hierarchy = (node(root, *children),)

    objects = CandidateObjectGrouperV1().group(
        hierarchy,
        roi_width=1917,
        roi_height=1152,
    )

    assert objects == []


def test_does_not_collapse_nested_container():
    root = candidate(
        100,
        Rect(100, 100, 100, 60),
    )

    child = candidate(
        101,
        Rect(105, 105, 90, 50),
        parent=100,
        depth=1,
    )

    grandchild = candidate(
        102,
        Rect(110, 110, 80, 40),
        parent=101,
        depth=2,
    )

    hierarchy = (
        node(
            root,
            node(
                child,
                node(grandchild),
            ),
        ),
    )

    objects = CandidateObjectGrouperV1().group(
        hierarchy,
        roi_width=1917,
        roi_height=1152,
    )

    assert objects == []
