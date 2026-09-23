from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.logical_object_graph import LogicalObjectGraph
from app.runtime.execution.vision.models.logical_object_relationship import (
    LogicalObjectRelationship,
)
from app.runtime.execution.vision.models.logical_object_relationship_type import (
    LogicalObjectRelationshipType,
)
from app.runtime.execution.vision.models.rect import Rect


def make_object(x: int, y: int, width: int, height: int) -> LogicalObject:
    return LogicalObject(
        bounds=Rect(x=x, y=y, width=width, height=height),
        root_contour_index=1,
        member_contour_indices=(1,),
    )


def test_graph_stores_logical_objects() -> None:
    graph = LogicalObjectGraph()

    parent = make_object(10, 10, 100, 50)
    child = make_object(20, 20, 40, 20)

    graph.add_object("parent", parent)
    graph.add_object("child", child)

    assert graph.objects["parent"] is parent
    assert graph.objects["child"] is child
    assert len(graph.objects) == 2


def test_graph_stores_contains_relationship() -> None:
    graph = LogicalObjectGraph()

    graph.add_object("parent", make_object(10, 10, 100, 50))
    graph.add_object("child", make_object(20, 20, 40, 20))

    relationship = LogicalObjectRelationship(
        source_id="parent",
        target_id="child",
        relationship_type=LogicalObjectRelationshipType.CONTAINS,
        confidence=0.92,
        iou=0.46,
        shared_component_count=4,
    )

    graph.add_relationship(relationship)

    assert graph.relationships == [relationship]


def test_graph_resolves_children_and_parents() -> None:
    graph = LogicalObjectGraph()

    graph.add_object("parent", make_object(10, 10, 100, 50))
    graph.add_object("child", make_object(20, 20, 40, 20))

    graph.add_relationship(
        LogicalObjectRelationship(
            source_id="parent",
            target_id="child",
            relationship_type=LogicalObjectRelationshipType.CONTAINS,
        )
    )

    assert graph.get_children("parent") == ("child",)
    assert graph.get_parents("child") == ("parent",)


def test_graph_supports_non_hierarchical_relationships() -> None:
    graph = LogicalObjectGraph()

    graph.add_object("left", make_object(10, 10, 30, 30))
    graph.add_object("right", make_object(45, 10, 30, 30))

    relationship = LogicalObjectRelationship(
        source_id="left",
        target_id="right",
        relationship_type=LogicalObjectRelationshipType.ADJACENT,
        confidence=0.81,
    )

    graph.add_relationship(relationship)

    assert graph.get_relationships_from("left") == (relationship,)
    assert graph.get_relationships_to("right") == (relationship,)
    assert graph.get_children("left") == ()
    assert graph.get_parents("right") == ()


def test_graph_rejects_duplicate_object_id() -> None:
    graph = LogicalObjectGraph()

    graph.add_object("object-1", make_object(10, 10, 30, 30))

    try:
        graph.add_object("object-1", make_object(20, 20, 40, 40))
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Expected duplicate object ID to raise ValueError")


def test_graph_rejects_unknown_relationship_source() -> None:
    graph = LogicalObjectGraph()

    graph.add_object("target", make_object(20, 20, 40, 40))

    relationship = LogicalObjectRelationship(
        source_id="missing",
        target_id="target",
        relationship_type=LogicalObjectRelationshipType.CONTAINS,
    )

    try:
        graph.add_relationship(relationship)
    except ValueError as exc:
        assert "Unknown source logical object" in str(exc)
    else:
        raise AssertionError("Expected unknown source to raise ValueError")


def test_graph_rejects_unknown_relationship_target() -> None:
    graph = LogicalObjectGraph()

    graph.add_object("source", make_object(10, 10, 30, 30))

    relationship = LogicalObjectRelationship(
        source_id="source",
        target_id="missing",
        relationship_type=LogicalObjectRelationshipType.CONTAINS,
    )

    try:
        graph.add_relationship(relationship)
    except ValueError as exc:
        assert "Unknown target logical object" in str(exc)
    else:
        raise AssertionError("Expected unknown target to raise ValueError")
