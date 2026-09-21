from app.runtime.execution.vision.analyzers.candidate_hierarchy import (
    CandidateHierarchy,
)
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.vision_candidate import (
    VisionCandidate,
)


def candidate(
    contour_index: int,
    parent_contour_index: int | None,
    depth: int,
    x: int,
) -> VisionCandidate:
    return VisionCandidate(
        rect=Rect(
            x=x,
            y=x,
            width=20,
            height=20,
        ),
        contour_index=contour_index,
        parent_contour_index=parent_contour_index,
        depth=depth,
    )


def test_builds_parent_child_relationship():
    root = candidate(
        contour_index=0,
        parent_contour_index=None,
        depth=0,
        x=10,
    )

    child = candidate(
        contour_index=1,
        parent_contour_index=0,
        depth=1,
        x=20,
    )

    result = CandidateHierarchy().build([root, child])

    assert len(result) == 1

    tree_root = result[0]

    assert tree_root.contour_index == 0
    assert tree_root.depth == 0

    assert len(tree_root.children) == 1
    assert tree_root.children[0].contour_index == 1
    assert tree_root.children[0].depth == 1


def test_builds_multi_level_hierarchy():
    root = candidate(
        contour_index=0,
        parent_contour_index=None,
        depth=0,
        x=10,
    )

    child = candidate(
        contour_index=1,
        parent_contour_index=0,
        depth=1,
        x=20,
    )

    grandchild = candidate(
        contour_index=2,
        parent_contour_index=1,
        depth=2,
        x=30,
    )

    result = CandidateHierarchy().build(
        [root, child, grandchild]
    )

    assert len(result) == 1

    tree_root = result[0]
    assert tree_root.contour_index == 0

    tree_child = tree_root.children[0]
    assert tree_child.contour_index == 1

    tree_grandchild = tree_child.children[0]
    assert tree_grandchild.contour_index == 2

    assert tree_grandchild.children == ()


def test_promotes_candidate_when_parent_was_filtered_out():
    child = candidate(
        contour_index=5,
        parent_contour_index=2,
        depth=1,
        x=50,
    )

    result = CandidateHierarchy().build([child])

    assert len(result) == 1

    promoted = result[0]

    assert promoted.contour_index == 5
    assert promoted.children == ()
