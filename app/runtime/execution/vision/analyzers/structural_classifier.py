from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.rect import Rect


@dataclass(frozen=True, slots=True)
class StructuralClassifierConfig:
    """
    Geometry-only thresholds used to recognize structural GUI regions.

    These values intentionally describe proportions rather than absolute
    pixel sizes so the classifier can later work with different DPI/scales.
    """

    toolbar_min_width_ratio: float = 0.45
    toolbar_max_height_ratio: float = 0.20
    toolbar_min_aspect_ratio: float = 4.0

    vertical_toolbar_min_height_ratio: float = 0.45
    vertical_toolbar_max_width_ratio: float = 0.20

    canvas_min_area_ratio: float = 0.08
    canvas_min_aspect_ratio: float = 0.70
    canvas_max_aspect_ratio: float = 1.45
    canvas_max_children: int = 1

    panel_min_area_ratio: float = 0.10
    panel_min_children: int = 1

    section_min_area_ratio: float = 0.03
    section_min_children: int = 2


@dataclass(frozen=True, slots=True)
class StructuralClassification:
    """
    Result of geometry-only structural classification.

    child_count describes how many candidate rectangles are structurally
    contained by the candidate. It is useful later when building the
    actual SceneGraph hierarchy.
    """

    control_type: ControlType
    confidence: float
    child_count: int

    @property
    def is_container(self) -> bool:
        return self.control_type in {
            ControlType.TOOLBAR,
            ControlType.PANEL,
            ControlType.SECTION,
            ControlType.GROUP,
            ControlType.CANVAS,
        }


class StructuralClassifier:
    """
    Classifies candidate rectangles into coarse GUI structures.

    This class deliberately does NOT attempt to identify semantic controls
    such as BUTTON, CHECKBOX or TEXT_FIELD.

    Its job is to answer a simpler question:

        "Does this rectangle look like part of the GUI structure?"

    The classifier uses only:
    - candidate geometry,
    - relative size,
    - aspect ratio,
    - containment relationships.

    No OCR, templates or application-specific rules are used here.
    """

    def __init__(
        self,
        config: StructuralClassifierConfig | None = None,
    ) -> None:
        self.config = config or StructuralClassifierConfig()

    def classify(
        self,
        candidates: list[Rect],
        *,
        roi_width: int,
        roi_height: int,
    ) -> list[StructuralClassification]:
        """
        Classify candidates in their original order.
        """

        if roi_width <= 0 or roi_height <= 0:
            return [
                StructuralClassification(
                    control_type=ControlType.UNKNOWN,
                    confidence=0.0,
                    child_count=0,
                )
                for _ in candidates
            ]

        child_counts = self._child_counts(candidates)

        return [
            self._classify_one(
                rect,
                child_count=child_counts[index],
                roi_width=roi_width,
                roi_height=roi_height,
            )
            for index, rect in enumerate(candidates)
        ]

    def _classify_one(
        self,
        rect: Rect,
        *,
        child_count: int,
        roi_width: int,
        roi_height: int,
    ) -> StructuralClassification:
        area_ratio = rect.area / (roi_width * roi_height)

        width_ratio = rect.width / roi_width
        height_ratio = rect.height / roi_height

        aspect_ratio = self._aspect_ratio(rect)

        # --------------------------------------------------------------
        # Horizontal toolbar
        # --------------------------------------------------------------
        if (
            width_ratio >= self.config.toolbar_min_width_ratio
            and height_ratio <= self.config.toolbar_max_height_ratio
            and aspect_ratio >= self.config.toolbar_min_aspect_ratio
        ):
            confidence = 0.90

            if child_count >= 1:
                confidence += 0.05

            return StructuralClassification(
                control_type=ControlType.TOOLBAR,
                confidence=min(confidence, 0.98),
                child_count=child_count,
            )

        # --------------------------------------------------------------
        # Vertical toolbar
        # --------------------------------------------------------------
        if (
            height_ratio >= self.config.vertical_toolbar_min_height_ratio
            and width_ratio <= self.config.vertical_toolbar_max_width_ratio
            and aspect_ratio >= self.config.toolbar_min_aspect_ratio
        ):
            confidence = 0.90

            if child_count >= 1:
                confidence += 0.05

            return StructuralClassification(
                control_type=ControlType.TOOLBAR,
                confidence=min(confidence, 0.98),
                child_count=child_count,
            )

        # --------------------------------------------------------------
        # Canvas
        #
        # A large, relatively square area with little internal structure
        # is a useful generic signal for a drawing/work area.
        # --------------------------------------------------------------
        if (
            area_ratio >= self.config.canvas_min_area_ratio
            and self.config.canvas_min_aspect_ratio
            <= aspect_ratio
            <= self.config.canvas_max_aspect_ratio
            and child_count <= self.config.canvas_max_children
        ):
            return StructuralClassification(
                control_type=ControlType.CANVAS,
                confidence=0.88,
                child_count=child_count,
            )

        # --------------------------------------------------------------
        # Large panel containing other candidates
        # --------------------------------------------------------------
        if (
            area_ratio >= self.config.panel_min_area_ratio
            and child_count >= self.config.panel_min_children
        ):
            confidence = 0.82

            if child_count >= 2:
                confidence += 0.08

            return StructuralClassification(
                control_type=ControlType.PANEL,
                confidence=min(confidence, 0.96),
                child_count=child_count,
            )

        # --------------------------------------------------------------
        # Smaller structural section/group
        # --------------------------------------------------------------
        if (
            area_ratio >= self.config.section_min_area_ratio
            and child_count >= self.config.section_min_children
        ):
            return StructuralClassification(
                control_type=ControlType.SECTION,
                confidence=0.80,
                child_count=child_count,
            )

        # --------------------------------------------------------------
        # We don't know enough yet.
        #
        # This is intentional. UNKNOWN is much safer than inventing
        # a semantic control type.
        # --------------------------------------------------------------
        return StructuralClassification(
            control_type=ControlType.UNKNOWN,
            confidence=0.40,
            child_count=child_count,
        )

    @staticmethod
    def _aspect_ratio(rect: Rect) -> float:
        smallest = max(1, min(rect.width, rect.height))
        largest = max(rect.width, rect.height)
        return largest / smallest

    @classmethod
    def _child_counts(cls, candidates: list[Rect]) -> list[int]:
        """
        Count structural children.

        We first determine the smallest candidate that contains each
        candidate. This avoids counting every ancestor as a direct child.

        Example:

            PANEL
              └── SECTION
                    └── BUTTON

        The PANEL gets one direct child (SECTION), not two.
        """

        parent_indices: list[int | None] = [None] * len(candidates)

        for child_index, child in enumerate(candidates):
            best_parent: int | None = None
            best_parent_area: int | None = None

            for parent_index, parent in enumerate(candidates):
                if parent_index == child_index:
                    continue

                if parent.area <= child.area:
                    continue

                if not cls._strictly_contains(parent, child):
                    continue

                if (
                    best_parent_area is None
                    or parent.area < best_parent_area
                ):
                    best_parent = parent_index
                    best_parent_area = parent.area

            parent_indices[child_index] = best_parent

        counts = [0] * len(candidates)

        for parent_index in parent_indices:
            if parent_index is not None:
                counts[parent_index] += 1

        return counts

    @staticmethod
    def _strictly_contains(outer: Rect, inner: Rect) -> bool:
        """
        True when outer fully contains inner and they are not identical.
        """

        return (
            outer.left <= inner.left
            and outer.top <= inner.top
            and outer.right >= inner.right
            and outer.bottom >= inner.bottom
            and outer.area > inner.area
        )
