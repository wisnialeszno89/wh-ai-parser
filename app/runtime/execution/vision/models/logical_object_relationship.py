from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.logical_object_relationship_type import (
    LogicalObjectRelationshipType,
)


@dataclass(frozen=True, slots=True)
class LogicalObjectRelationship:
    """
    Relationship between two logical visual objects.

    This layer describes only spatial/structural relationships.
    It does not assign semantic GUI meaning.
    """

    source_id: str
    target_id: str
    relationship_type: LogicalObjectRelationshipType

    confidence: float = 1.0
    iou: float | None = None
    shared_component_count: int = 0
