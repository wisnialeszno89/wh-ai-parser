from app.runtime.execution.vision.analyzers.layout_structure_detector_v1 import (
    LayoutStructureDetectorV1,
)
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect


def make_object(index: int, x: int, y: int, width: int, height: int):
    return LogicalObject(
        bounds=Rect(x, y, width, height),
        root_contour_index=index,
        member_contour_indices=(index,),
    )


def test_detects_horizontal_row():
    objects = (
        make_object(1, 10, 10, 50, 30),
        make_object(2, 70, 12, 50, 30),
        make_object(3, 130, 10, 50, 30),
    )

    structures = LayoutStructureDetectorV1().detect(objects)

    assert len(structures) == 1
    assert structures[0].kind == "horizontal_row"
    assert structures[0].object_indices == (0, 1, 2)


def test_detects_vertical_stack():
    objects = (
        make_object(1, 10, 10, 50, 30),
        make_object(2, 12, 55, 50, 30),
        make_object(3, 10, 100, 50, 30),
    )

    structures = LayoutStructureDetectorV1().detect(objects)

    assert len(structures) == 1
    assert structures[0].kind == "vertical_stack"
    assert structures[0].object_indices == (0, 1, 2)


def test_detects_isolated_object():
    objects = (
        make_object(1, 10, 10, 30, 30),
    )

    structures = LayoutStructureDetectorV1().detect(objects)

    assert len(structures) == 1
    assert structures[0].kind == "isolated"
    assert structures[0].object_indices == (0,)


def test_does_not_merge_diagonal_objects():
    objects = (
        make_object(1, 10, 10, 30, 30),
        make_object(2, 100, 100, 30, 30),
    )

    structures = LayoutStructureDetectorV1().detect(objects)

    assert len(structures) == 2
    assert structures[0].kind == "isolated"
    assert structures[1].kind == "isolated"


def test_detects_two_dimensional_grid():
    objects = (
        make_object(1, 10, 10, 40, 30),
        make_object(2, 60, 10, 40, 30),
        make_object(3, 10, 50, 40, 30),
        make_object(4, 60, 50, 40, 30),
    )

    structures = LayoutStructureDetectorV1().detect(objects)

    assert len(structures) == 1
    assert structures[0].kind == "grid"
    assert structures[0].object_indices == (0, 1, 2, 3)


def test_does_not_create_grid_from_unrelated_rows():
    objects = (
        # Upper UI group.
        make_object(1, 8, 88, 475, 41),
        make_object(2, 208, 89, 36, 36),
        make_object(3, 250, 96, 23, 22),
        make_object(4, 412, 93, 22, 28),

        # Separate lower row with unrelated objects.
        make_object(5, 111, 175, 65, 33),
        make_object(6, 177, 175, 49, 33),
        make_object(7, 375, 175, 81, 33),
        make_object(8, 457, 175, 115, 33),
        make_object(9, 573, 175, 81, 33),
        make_object(10, 655, 175, 165, 33),
        make_object(11, 1135, 175, 97, 33),
        make_object(12, 1233, 175, 97, 33),
    )

    structures = LayoutStructureDetectorV1().detect(objects)

    assert all(structure.kind != "grid" for structure in structures)
