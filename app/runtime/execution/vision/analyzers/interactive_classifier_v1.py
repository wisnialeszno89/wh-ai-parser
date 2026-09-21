from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.candidate_evidence import (
    CandidateEvidence,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)


@dataclass(frozen=True, slots=True)
class InteractiveClassification:
    """
    Result of interactive-control classification.

    The classifier identifies what kind of interactive GUI control
    a candidate most likely represents.

    Semantic application-specific roles are intentionally resolved
    by a later layer.
    """

    control_type: ControlType
    confidence: float

    @property
    def is_interactive(self) -> bool:
        return self.control_type in {
            ControlType.BUTTON,
            ControlType.TEXT_FIELD,
            ControlType.CHECKBOX,
            ControlType.RADIO_BUTTON,
            ControlType.COMBO_BOX,
            ControlType.LIST,
            ControlType.TABLE,
            ControlType.TREE,
        }


class InteractiveClassifierV1:
    """
    Classifies visual candidates into generic interactive GUI controls.

    V1 intentionally starts with a conservative contract.
    It does not use OCR, application-specific labels or WindowHub rules.
    """

    def classify(
        self,
        evidence: CandidateEvidence,
    ) -> InteractiveClassification:
        if self._looks_like_button(evidence):
            return InteractiveClassification(
                control_type=ControlType.BUTTON,
                confidence=0.75,
            )

        return InteractiveClassification(
            control_type=ControlType.UNKNOWN,
            confidence=0.0,
        )

    @staticmethod
    def _looks_like_button(evidence: CandidateEvidence) -> bool:
        candidate = evidence.candidate
        visual = evidence.visual

        return (
            2.0 <= candidate.aspect_ratio <= 6.0
            and 0.005 <= candidate.area_ratio <= 0.08
            and candidate.child_count >= 1
            and visual.edge_density >= 0.15
            and visual.border_edge_density >= 0.05
            and visual.interior_content_density >= 0.05
        )
