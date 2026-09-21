from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.candidate_features import (
    CandidateFeatures,
)
from app.runtime.execution.vision.models.visual_features import (
    VisualFeatures,
)


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    """
    Combined low-level evidence describing a vision candidate.

    CandidateFeatures describe geometry and structural context.
    VisualFeatures describe pixel-level visual characteristics.

    This model intentionally does not assign semantic UI meaning.
    """

    candidate: CandidateFeatures
    visual: VisualFeatures
