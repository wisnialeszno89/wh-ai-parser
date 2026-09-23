from __future__ import annotations

from dataclasses import dataclass, field

from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.logical_object_relationship import (
    LogicalObjectRelationship,
)
from app.runtime.execution.vision.models.logical_object_relationship_type import (
    LogicalObjectRelationshipType,
)


@dataclass(slots=True)
class LogicalObjectGraph:
    """
    Graph of reconstructed logical visual objects.

    Nodes are LogicalObjects.
    Edges are explicit spatial/structural relationships.

    The graph intentionally remains independent from semantic GUI meaning.
    """

    objects: dict[str, LogicalObject] = field(default_factory=dict)
    relationships: list[LogicalObjectRelationship] = field(default_factory=list)

    def add_object(self, object_id: str, logical_object: LogicalObject) -> None:
        if object_id in self.objects:
            raise ValueError(f"Logical object already exists: {object_id}")

        self.objects[object_id] = logical_object

    def add_relationship(
        self,
        relationship: LogicalObjectRelationship,
    ) -> None:
        if relationship.source_id not in self.objects:
            raise ValueError(
                f"Unknown source logical object: {relationship.source_id}"
            )

        if relationship.target_id not in self.objects:
            raise ValueError(
                f"Unknown target logical object: {relationship.target_id}"
            )

        self.relationships.append(relationship)

    def get_relationships_from(
        self,
        object_id: str,
    ) -> tuple[LogicalObjectRelationship, ...]:
        return tuple(
            relationship
            for relationship in self.relationships
            if relationship.source_id == object_id
        )

    def get_relationships_to(
        self,
        object_id: str,
    ) -> tuple[LogicalObjectRelationship, ...]:
        return tuple(
            relationship
            for relationship in self.relationships
            if relationship.target_id == object_id
        )

    def get_children(
        self,
        object_id: str,
    ) -> tuple[str, ...]:
        return tuple(
            relationship.target_id
            for relationship in self.get_relationships_from(object_id)
            if relationship.relationship_type
            == LogicalObjectRelationshipType.CONTAINS
        )

    def get_parents(
        self,
        object_id: str,
    ) -> tuple[str, ...]:
        return tuple(
            relationship.source_id
            for relationship in self.get_relationships_to(object_id)
            if relationship.relationship_type
            == LogicalObjectRelationshipType.CONTAINS
        )
