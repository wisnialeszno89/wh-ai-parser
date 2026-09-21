from __future__ import annotations

from collections import Counter

from app.runtime.execution.vision.analyzers.candidate_hierarchy import CandidateHierarchy
from app.runtime.execution.vision.models.candidate_features import CandidateFeatures
from app.runtime.execution.vision.models.vision_candidate import VisionCandidate


class CandidateFeatureExtractor:
    """
    Converts geometric VisionCandidates into richer feature descriptions.

    This layer intentionally does not classify candidates as BUTTON,
    PANEL, CANVAS, etc.

    Hierarchical information is derived from CandidateHierarchy so that
    feature extraction does not maintain a second, independent hierarchy
    implementation.
    """

    def __init__(self, candidate_hierarchy: CandidateHierarchy | None = None):
        self.candidate_hierarchy = candidate_hierarchy or CandidateHierarchy()

    def extract(
        self,
        candidates: list[VisionCandidate],
        *,
        roi_width: int,
        roi_height: int,
    ) -> list[CandidateFeatures]:

        if roi_width <= 0 or roi_height <= 0:
            return []

        if not candidates:
            return []

        roi_area = roi_width * roi_height

        sibling_counts = self._sibling_counts(candidates)
        child_counts = self._child_counts(candidates)

        return [
            self._extract_one(
                candidate,
                roi_width=roi_width,
                roi_height=roi_height,
                roi_area=roi_area,
                sibling_count=sibling_counts[index],
                child_count=child_counts.get(candidate.contour_index, 0),
            )
            for index, candidate in enumerate(candidates)
        ]

    def _extract_one(
        self,
        candidate: VisionCandidate,
        *,
        roi_width: int,
        roi_height: int,
        roi_area: int,
        sibling_count: int,
        child_count: int,
    ) -> CandidateFeatures:

        rect = candidate.rect

        width = rect.width
        height = rect.height
        area = rect.area

        aspect_ratio = width / height if height else 0.0

        return CandidateFeatures(
            width=width,
            height=height,
            area=area,
            aspect_ratio=aspect_ratio,
            area_ratio=area / roi_area,
            width_ratio=width / roi_width,
            height_ratio=height / roi_height,
            center_x=(rect.x + width / 2) / roi_width,
            center_y=(rect.y + height / 2) / roi_height,
            depth=candidate.depth,
            child_count=child_count,
            sibling_count=sibling_count,
            touches_left=rect.left <= 0,
            touches_right=rect.right >= roi_width,
            touches_top=rect.top <= 0,
            touches_bottom=rect.bottom >= roi_height,
        )

    def _child_counts(
        self,
        candidates: list[VisionCandidate],
    ) -> dict[int, int]:

        tree = self.candidate_hierarchy.build(candidates)

        counts: dict[int, int] = {}

        def visit(node) -> None:
            counts[node.contour_index] = len(node.children)

            for child in node.children:
                visit(child)

        for root in tree:
            visit(root)

        return counts

    @staticmethod
    def _sibling_counts(
        candidates: list[VisionCandidate],
    ) -> dict[int, int]:

        parent_counts = Counter(
            candidate.parent_contour_index
            for candidate in candidates
        )

        return {
            index: max(
                0,
                parent_counts[candidate.parent_contour_index] - 1,
            )
            for index, candidate in enumerate(candidates)
        }
