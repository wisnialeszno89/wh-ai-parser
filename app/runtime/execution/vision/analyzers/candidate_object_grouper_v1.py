from dataclasses import dataclass

from app.runtime.execution.vision.analyzers.candidate_hierarchy import (
    CandidateHierarchy,
    CandidateNode,
)
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect


@dataclass(frozen=True, slots=True)
class CandidateObjectGrouperConfig:
    """
    Generic structural limits for compound-object reconstruction.

    These limits intentionally describe visual structure rather than
    application-specific controls.
    """

    max_children: int = 4
    max_area_ratio: float = 0.03
    max_child_depth: int = 1


class CandidateObjectGrouperV1:
    """
    Reconstruct logical visual objects from the candidate hierarchy.

    V1 groups a candidate with its direct children when the structure
    looks like a compact compound visual object.

    Large containers and deeply nested structures remain ungrouped so
    that later container reconstruction can handle them separately.
    """

    def __init__(
        self,
        config: CandidateObjectGrouperConfig | None = None,
    ) -> None:
        self.config = config or CandidateObjectGrouperConfig()

    def group(
        self,
        hierarchy: tuple[CandidateNode, ...],
        *,
        roi_width: int,
        roi_height: int,
    ) -> list[LogicalObject]:
        if not hierarchy or roi_width <= 0 or roi_height <= 0:
            return []

        objects: list[LogicalObject] = []

        for root, blocked_by_compact_ancestor in self._walk(
            hierarchy,
            roi_width=roi_width,
            roi_height=roi_height,
        ):
            if blocked_by_compact_ancestor:
                continue

            if not self._is_compound_candidate(
                root,
                roi_width=roi_width,
                roi_height=roi_height,
            ):
                continue

            members = [root.candidate]

            for child in root.children:
                members.append(child.candidate)

            bounds = self._union_bounds(
                candidate.rect for candidate in members
            )

            objects.append(
                LogicalObject(
                    bounds=bounds,
                    root_contour_index=root.contour_index,
                    member_contour_indices=tuple(
                        candidate.contour_index
                        for candidate in members
                    ),
                )
            )

        return objects

    def _is_compound_candidate(
        self,
        node: CandidateNode,
        *,
        roi_width: int,
        roi_height: int,
    ) -> bool:
        children = node.children

        if not children:
            return False

        if len(children) > self.config.max_children:
            return False

        if node.candidate.depth > self.config.max_child_depth:
            return False

        area_ratio = (
            node.candidate.rect.area
            / float(roi_width * roi_height)
        )

        if area_ratio > self.config.max_area_ratio:
            return False

        # V1 only groups direct children that are leaves.
        # This prevents large nested containers from collapsing into
        # a single logical control.
        if any(child.children for child in children):
            return False

        return True

    @staticmethod
    def _union_bounds(rects) -> Rect:
        rects = tuple(rects)

        left = min(rect.x for rect in rects)
        top = min(rect.y for rect in rects)
        right = max(rect.right for rect in rects)
        bottom = max(rect.bottom for rect in rects)

        return Rect(
            x=left,
            y=top,
            width=right - left,
            height=bottom - top,
        )

    def _walk(
        self,
        nodes: tuple[CandidateNode, ...],
        *,
        roi_width: int,
        roi_height: int,
        blocked_by_compact_ancestor: bool = False,
    ):
        for node in nodes:
            yield node, blocked_by_compact_ancestor

            compact_parent = self._is_compact_parent(
                node,
                roi_width=roi_width,
                roi_height=roi_height,
            )

            yield from self._walk(
                node.children,
                roi_width=roi_width,
                roi_height=roi_height,
                blocked_by_compact_ancestor=(
                    blocked_by_compact_ancestor or compact_parent
                ),
            )

    def _is_compact_parent(
        self,
        node: CandidateNode,
        *,
        roi_width: int,
        roi_height: int,
    ) -> bool:
        if not node.children:
            return False

        if len(node.children) > self.config.max_children:
            return False

        area_ratio = (
            node.candidate.rect.area
            / float(roi_width * roi_height)
        )

        return area_ratio <= self.config.max_area_ratio
