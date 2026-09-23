from app.runtime.execution.vision.analyzers.logical_object_graph_builder import (
    LogicalObjectGraphBuilder,
)
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.logical_object_relationship_type import (
    LogicalObjectRelationshipType,
)
from app.runtime.execution.vision.models.rect import Rect


def make_object(
    x: int,
    y: int,
    width: int,
    height: int,
    root: int,
    members: tuple[int, ...],
) -> LogicalObject:
    return LogicalObject(
        bounds=Rect(
            x=x,
            y=y,
            width=width,
            height=height,
        ),
        root_contour_index=root,
        member_contour_indices=members,
    )


def test_builder_creates_graph_nodes() -> None:
    objects = [
        make_object(10, 10, 100, 50, 1, (1,)),
        make_object(20, 20, 30, 20, 2, (2,)),
    ]

    graph = LogicalObjectGraphBuilder().build(objects)

    assert len(graph.objects) == 2
    assert graph.objects["LO-0001"] == objects[0]
    assert graph.objects["LO-0002"] == objects[1]


def test_builder_detects_contains_relationship() -> None:
    objects = [
        make_object(10, 10, 100, 50, 1, (1,)),
        make_object(20, 20, 30, 20, 2, (2,)),
    ]

    graph = LogicalObjectGraphBuilder().build(objects)

    relationships = graph.get_relationships_from("LO-0001")

    assert len(relationships) == 1
    assert relationships[0].relationship_type == (
        LogicalObjectRelationshipType.CONTAINS
    )
    assert relationships[0].target_id == "LO-0002"


def test_builder_preserves_shared_content_metadata() -> None:
    objects = [
        make_object(10, 10, 50, 30, 1, (1, 2, 3)),
        make_object(12, 12, 40, 20, 2, (2, 3, 4)),
    ]

    graph = LogicalObjectGraphBuilder().build(objects)

    relationships = graph.relationships

    assert len(relationships) == 1
    assert relationships[0].relationship_type == (
        LogicalObjectRelationshipType.CONTAINS
    )
    assert relationships[0].shared_component_count == 2


def test_builder_detects_overlap() -> None:
    objects = [
        make_object(10, 10, 40, 40, 1, (1,)),
        make_object(30, 30, 40, 40, 2, (2,)),
    ]

    graph = LogicalObjectGraphBuilder(
        overlap_threshold=0.05
    ).build(objects)

    assert len(graph.relationships) == 1
    assert graph.relationships[0].relationship_type == (
        LogicalObjectRelationshipType.OVERLAPS
    )


def test_builder_does_not_create_relationship_for_separate_objects() -> None:
    objects = [
        make_object(10, 10, 20, 20, 1, (1,)),
        make_object(100, 100, 20, 20, 2, (2,)),
    ]

    graph = LogicalObjectGraphBuilder().build(objects)

    assert graph.relationships == []


def test_builder_does_not_create_mutual_contains_for_identical_bounds() -> None:
    objects = [
        make_object(10, 10, 40, 40, 1, (1,)),
        make_object(10, 10, 40, 40, 2, (2,)),
    ]

    graph = LogicalObjectGraphBuilder().build(objects)

    assert len(graph.relationships) <= 1
