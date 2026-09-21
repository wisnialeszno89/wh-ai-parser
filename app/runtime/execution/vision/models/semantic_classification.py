from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.control_role import ControlRole
from app.runtime.execution.vision.models.control_type import ControlType


@dataclass(frozen=True, slots=True)
class SemanticClassification:
    """
    Semantic interpretation of a detected GUI candidate.

    The classification is intentionally separate from low-level
    CandidateEvidence and coarse structural classification.
    """

    control_type: ControlType
    role: ControlRole
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
