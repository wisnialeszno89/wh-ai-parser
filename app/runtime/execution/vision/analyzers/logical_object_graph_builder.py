from __future__ import annotations

from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.logical_object_graph import LogicalObjectGraph
from app.runtime.execution.vision.models.logical_object_relationship import (
    LogicalObjectRelationship,
)
from app.runtime.execution.vision.models.logical_object_relationship_type import (
    LogicalObjectRelationshipType,
)


class LogicalObjectGraphBuilder:
    """
    Builds a relationship graph from reconstructed LogicalObjects.

    This builder is intentionally semantic-free. It uses only:
    - geometry,
    - intersection / IoU,
    - contour membership.

    Semantic GUI meaning is assigned later.
    """

    def __init__(self, overlap_threshold: float = 0.15) -> None:
        if not 0.0 <= overlap_threshold <= 1.0:
            raise ValueError("overlap_threshold must be between 0 and 1")

        self.overlap_threshold = overlap_threshold

    def build(
        self,
        objects: list[LogicalObject],
    ) -> LogicalObjectGraph:
        graph = LogicalObjectGraph()

        for index, logical_object in enumerate(objects, start=1):
            object_id = f"LO-{index:04d}"
            graph.add_object(object_id, logical_object)

        items = list(graph.objects.items())

        for index, (source_id, source) in enumerate(items):
            for target_id, target in items[index + 1:]:
                self._add_relationships(
                    graph,
                    source_id,
                    source,
                    target_id,
                    target,
                )

        return graph

    def _add_relationships(
        self,
        graph: LogicalObjectGraph,
        source_id: str,
        source: LogicalObject,
        target_id: str,
        target: LogicalObject,
    ) -> None:
        source_rect = source.bounds
        target_rect = target.bounds

        source_contains_target = self._contains(
            source_rect,
            target_rect,
        )
        target_contains_source = self._contains(
            target_rect,
            source_rect,
        )

        iou = self._iou(source_rect, target_rect)

        shared_components = set(
            source.member_contour_indices
        ).intersection(
            target.member_contour_indices
        )

        if source_contains_target and source_rect != target_rect:
            graph.add_relationship(
                LogicalObjectRelationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=LogicalObjectRelationshipType.CONTAINS,
                    confidence=self._containment_confidence(
                        source_rect,
                        target_rect,
                    ),
                    iou=iou,
                    shared_component_count=len(shared_components),
                )
            )

        elif target_contains_source and source_rect != target_rect:
            graph.add_relationship(
                LogicalObjectRelationship(
                    source_id=target_id,
                    target_id=source_id,
                    relationship_type=LogicalObjectRelationshipType.CONTAINS,
                    confidence=self._containment_confidence(
                        target_rect,
                        source_rect,
                    ),
                    iou=iou,
                    shared_component_count=len(shared_components),
                )
            )

        elif iou >= self.overlap_threshold:
            graph.add_relationship(
                LogicalObjectRelationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=LogicalObjectRelationshipType.OVERLAPS,
                    confidence=min(iou, 1.0),
                    iou=iou,
                    shared_component_count=len(shared_components),
                )
            )

    @staticmethod
    def _contains(outer, inner) -> bool:
        return (
            outer.left <= inner.left
            and outer.top <= inner.top
            and outer.right >= inner.right
            and outer.bottom >= inner.bottom
        )

    @staticmethod
    def _intersection_area(first, second) -> int:
        left = max(first.left, second.left)
        top = max(first.top, second.top)
        right = min(first.right, second.right)
        bottom = min(first.bottom, second.bottom)

        if right <= left or bottom <= top:
            return 0

        return (right - left) * (bottom - top)

    @classmethod
    def _iou(cls, first, second) -> float:
        intersection = cls._intersection_area(first, second)

        if intersection == 0:
            return 0.0

        union = first.area + second.area - intersection

        if union <= 0:
            return 0.0

        return intersection / union

    @classmethod
    def _containment_confidence(cls, outer, inner) -> float:
        if outer.area <= 0:
            return 0.0

        return min(inner.area / outer.area, 1.0)
