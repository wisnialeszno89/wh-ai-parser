from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.candidate_features import (
    CandidateFeatures,
)
from app.runtime.execution.vision.models.control_type import ControlType


@dataclass(frozen=True, slots=True)
class StructuralClassifierV2Config:
    """
    Context-aware thresholds for coarse structural GUI classification.

    V2 operates on CandidateFeatures rather than raw rectangles.
    It intentionally does not classify interactive controls such as
    BUTTON, CHECKBOX or TEXT_FIELD.
    """

    toolbar_min_width_ratio: float = 0.45
    toolbar_max_height_ratio: float = 0.20
    toolbar_min_aspect_ratio: float = 4.0

    vertical_toolbar_min_height_ratio: float = 0.45
    vertical_toolbar_max_width_ratio: float = 0.20

    canvas_min_area_ratio: float = 0.04
    canvas_min_aspect_ratio: float = 0.70
    canvas_max_aspect_ratio: float = 1.45
    canvas_max_children: int = 1

    panel_min_area_ratio: float = 0.08
    panel_min_children: int = 1

    section_min_area_ratio: float = 0.025
    section_min_children: int = 2


@dataclass(frozen=True, slots=True)
class StructuralClassificationV2:
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


class StructuralClassifierV2:
    """
    Context-aware coarse structural classifier.

    V2 consumes CandidateFeatures, which means classification can use
    hierarchy, sibling context, position and ROI-relative geometry.

    It deliberately does NOT identify semantic interactive controls.
    """

    def __init__(
        self,
        config: StructuralClassifierV2Config | None = None,
    ) -> None:
        self.config = config or StructuralClassifierV2Config()

    def classify(
        self,
        features: list[CandidateFeatures],
    ) -> list[StructuralClassificationV2]:
        return [self._classify_one(feature) for feature in features]

    def _classify_one(
        self,
        feature: CandidateFeatures,
    ) -> StructuralClassificationV2:

        # --------------------------------------------------------------
        # Horizontal toolbar
        # --------------------------------------------------------------
        if (
            feature.width_ratio >= self.config.toolbar_min_width_ratio
            and feature.height_ratio <= self.config.toolbar_max_height_ratio
            and feature.aspect_ratio >= self.config.toolbar_min_aspect_ratio
        ):
            confidence = 0.86

            if feature.child_count >= 1:
                confidence += 0.06

            if feature.sibling_count >= 1:
                confidence += 0.03

            return self._result(
                ControlType.TOOLBAR,
                confidence,
                feature,
            )

        # --------------------------------------------------------------
        # Vertical toolbar
        # --------------------------------------------------------------
        if (
            feature.height_ratio >= self.config.vertical_toolbar_min_height_ratio
            and feature.width_ratio <= self.config.vertical_toolbar_max_width_ratio
            and feature.aspect_ratio <= 1.0 / self.config.toolbar_min_aspect_ratio
        ):
            confidence = 0.86

            if feature.child_count >= 1:
                confidence += 0.06

            if feature.sibling_count >= 1:
                confidence += 0.03

            return self._result(
                ControlType.TOOLBAR,
                confidence,
                feature,
            )

        # --------------------------------------------------------------
        # Canvas
        #
        # V1 required 8% of the complete ROI.
        #
        # V2 allows smaller square work areas, but requires low internal
        # structural complexity. This is important for the 317x317 and
        # similar WindowHub regions found in the benchmark.
        # --------------------------------------------------------------
        if (
            feature.area_ratio >= self.config.canvas_min_area_ratio
            and self.config.canvas_min_aspect_ratio
            <= feature.aspect_ratio
            <= self.config.canvas_max_aspect_ratio
            and feature.child_count <= self.config.canvas_max_children
        ):
            confidence = 0.80

            if feature.child_count == 0:
                confidence += 0.06

            if feature.sibling_count <= 2:
                confidence += 0.03

            return self._result(
                ControlType.CANVAS,
                confidence,
                feature,
            )

        # --------------------------------------------------------------
        # Panel
        #
        # Panels are large regions with internal structure.
        # --------------------------------------------------------------
        if (
            feature.area_ratio >= self.config.panel_min_area_ratio
            and feature.child_count >= self.config.panel_min_children
        ):
            confidence = 0.78

            if feature.child_count >= 2:
                confidence += 0.08

            if feature.depth == 0:
                confidence += 0.03

            return self._result(
                ControlType.PANEL,
                confidence,
                feature,
            )

        # --------------------------------------------------------------
        # Section
        #
        # A smaller structural container with multiple direct children.
        # --------------------------------------------------------------
        if (
            feature.area_ratio >= self.config.section_min_area_ratio
            and feature.child_count >= self.config.section_min_children
        ):
            confidence = 0.76

            if feature.child_count >= 3:
                confidence += 0.06

            return self._result(
                ControlType.SECTION,
                confidence,
                feature,
            )

        # --------------------------------------------------------------
        # UNKNOWN
        #
        # We deliberately keep uncertainty rather than inventing a type.
        # --------------------------------------------------------------
        return self._result(
            ControlType.UNKNOWN,
            0.40,
            feature,
        )

    @staticmethod
    def _result(
        control_type: ControlType,
        confidence: float,
        feature: CandidateFeatures,
    ) -> StructuralClassificationV2:

        return StructuralClassificationV2(
            control_type=control_type,
            confidence=min(confidence, 0.98),
            child_count=feature.child_count,
        )
