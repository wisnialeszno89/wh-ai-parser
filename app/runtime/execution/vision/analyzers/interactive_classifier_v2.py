from dataclasses import dataclass

from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.logical_object_evidence import (
    LogicalObjectEvidence,
)


@dataclass(frozen=True, slots=True)
class InteractiveClassificationV2:
    """
    Semantic classification produced from LogicalObjectEvidence.

    V2 is intentionally conservative. It currently recognizes only
    visually well-supported BUTTON and ICON patterns.
    """

    control_type: ControlType
    confidence: float

    @property
    def is_interactive(self) -> bool:
        return self.control_type == ControlType.BUTTON


@dataclass(frozen=True, slots=True)
class InteractiveClassifierV2Config:
    """
    Generic visual thresholds for compact interactive objects.

    These values describe visual structure rather than WindowHub
    semantics or labels.
    """

    button_min_aspect_ratio: float = 1.8
    button_max_aspect_ratio: float = 6.0
    button_min_width: int = 30
    button_max_height: int = 45
    button_min_edge_density: float = 0.20
    button_min_border_edge_density: float = 0.08
    button_max_interior_content_density: float = 0.25
    button_min_members: int = 2

    icon_min_aspect_ratio: float = 0.70
    icon_max_aspect_ratio: float = 1.30
    icon_max_width: int = 40
    icon_max_height: int = 40
    icon_min_edge_density: float = 0.18
    icon_min_interior_content_density: float = 0.30
    icon_min_members: int = 2


class InteractiveClassifierV2:
    """
    Classify reconstructed logical objects using geometry, hierarchy
    and visual evidence.

    The classifier deliberately avoids OCR and application-specific
    labels. Unknown remains a valid and preferred result when evidence
    is insufficient.
    """

    def __init__(
        self,
        config: InteractiveClassifierV2Config | None = None,
    ) -> None:
        self.config = config or InteractiveClassifierV2Config()

    def classify(
        self,
        evidence: LogicalObjectEvidence,
    ) -> InteractiveClassificationV2:
        if self._looks_like_button(evidence):
            return InteractiveClassificationV2(
                control_type=ControlType.BUTTON,
                confidence=self._button_confidence(evidence),
            )

        if self._looks_like_icon(evidence):
            return InteractiveClassificationV2(
                control_type=ControlType.ICON,
                confidence=self._icon_confidence(evidence),
            )

        return InteractiveClassificationV2(
            control_type=ControlType.UNKNOWN,
            confidence=0.0,
        )

    def _looks_like_button(
        self,
        evidence: LogicalObjectEvidence,
    ) -> bool:
        visual = evidence.visual
        config = self.config

        return (
            config.button_min_aspect_ratio
            <= evidence.aspect_ratio
            <= config.button_max_aspect_ratio
            and evidence.width >= config.button_min_width
            and evidence.height <= config.button_max_height
            and evidence.member_count >= config.button_min_members
            and visual.edge_density >= config.button_min_edge_density
            and visual.border_edge_density
            >= config.button_min_border_edge_density
            and visual.interior_content_density
            <= config.button_max_interior_content_density
        )

    def _looks_like_icon(
        self,
        evidence: LogicalObjectEvidence,
    ) -> bool:
        visual = evidence.visual
        config = self.config

        return (
            config.icon_min_aspect_ratio
            <= evidence.aspect_ratio
            <= config.icon_max_aspect_ratio
            and evidence.width <= config.icon_max_width
            and evidence.height <= config.icon_max_height
            and evidence.member_count >= config.icon_min_members
            and visual.edge_density >= config.icon_min_edge_density
            and visual.interior_content_density
            >= config.icon_min_interior_content_density
        )

    @staticmethod
    def _button_confidence(
        evidence: LogicalObjectEvidence,
    ) -> float:
        visual = evidence.visual

        score = 0.0
        score += min(visual.edge_density / 0.40, 1.0) * 0.35
        score += min(visual.border_edge_density / 0.15, 1.0) * 0.35
        score += min(
            evidence.member_count / 3.0,
            1.0,
        ) * 0.15
        score += max(
            0.0,
            1.0 - visual.interior_content_density / 0.25,
        ) * 0.15

        return round(min(score, 0.99), 3)

    @staticmethod
    def _icon_confidence(
        evidence: LogicalObjectEvidence,
    ) -> float:
        visual = evidence.visual

        score = 0.0
        score += min(visual.edge_density / 0.40, 1.0) * 0.40
        score += min(
            visual.interior_content_density / 0.70,
            1.0,
        ) * 0.40
        score += min(
            evidence.member_count / 3.0,
            1.0,
        ) * 0.20

        return round(min(score, 0.99), 3)
