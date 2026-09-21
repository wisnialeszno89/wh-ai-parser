from app.runtime.execution.vision.analyzers.logical_object_context_v1 import (
    LogicalObjectContextV1,
)
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect


def make_object(index: int, x: int, y: int, width: int, height: int):
    return LogicalObject(
        bounds=Rect(x, y, width, height),
        root_contour_index=index,
        member_contour_indices=(index,),
    )


def test_detects_left_and_right_neighbors():
    objects = (
        make_object(1, 10, 10, 50, 30),
        make_object(2, 80, 12, 50, 30),
        make_object(3, 150, 10, 50, 30),
    )

    contexts = LogicalObjectContextV1().analyze(objects)

    assert [n.object_index for n in contexts[1].left] == [0]
    assert [n.object_index for n in contexts[1].right] == [2]


def test_detects_above_and_below_neighbors():
    objects = (
        make_object(1, 10, 10, 50, 30),
        make_object(2, 12, 60, 50, 30),
        make_object(3, 10, 110, 50, 30),
    )

    contexts = LogicalObjectContextV1().analyze(objects)

    assert [n.object_index for n in contexts[1].above] == [0]
    assert [n.object_index for n in contexts[1].below] == [2]


def test_detects_same_row_and_same_column():
    objects = (
        make_object(1, 10, 10, 50, 30),
        make_object(2, 80, 12, 50, 30),
        make_object(3, 12, 60, 50, 30),
    )

    contexts = LogicalObjectContextV1().analyze(objects)

    assert contexts[0].same_row == (1,)
    assert contexts[0].same_column == (2,)


def test_ignores_diagonal_objects_without_alignment():
    objects = (
        make_object(1, 10, 10, 30, 30),
        make_object(2, 100, 100, 30, 30),
    )

    contexts = LogicalObjectContextV1().analyze(objects)

    assert contexts[0].left == ()
    assert contexts[0].right == ()
    assert contexts[0].above == ()
    assert contexts[0].below == ()
