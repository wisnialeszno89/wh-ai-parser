from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class EvidenceSource(str, Enum):
    ACCESSIBILITY = "accessibility"
    MEMORY = "memory"
    OCR = "ocr"
    SPATIAL = "spatial"
    VISUAL = "visual"
    TEMPORAL = "temporal"
    AI = "ai"


class EvidenceKind(str, Enum):
    CONTROL_TYPE = "control_type"
    TEXT = "text"
    LABEL = "label"
    ROLE = "role"
    BOUNDS = "bounds"
    POSITION = "position"
    RELATIONSHIP = "relationship"
    STABILITY = "stability"
    VISUAL_MATCH = "visual_match"
    SEMANTIC_NAME = "semantic_name"


@dataclass(frozen=True)
class SemanticEvidence:
    """
    A single piece of evidence about a visible element.

    Evidence describes what the robot has support for.
    It must not be confused with an inferred semantic conclusion.
    """

    source: EvidenceSource
    kind: EvidenceKind
    value: object

    confidence: float = 1.0

    element_id: str | None = None

    observed: bool = True

    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Evidence confidence must be between 0.0 and 1.0.")

        if not self.element_id and self.observed:
            raise ValueError(
                "Observed evidence must identify the screen element."
            )


@dataclass(frozen=True)
class SemanticCandidate:
    """
    A semantic hypothesis derived from one or more evidence items.

    A candidate is an inference, not an observed fact.
    """

    semantic_name: str
    confidence: float

    evidence: tuple[SemanticEvidence, ...] = ()

    element_id: str | None = None

    inferred: bool = True

    reason: str = ""

    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.semantic_name.strip():
            raise ValueError("Semantic candidate name cannot be empty.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Semantic candidate confidence must be between 0.0 and 1.0."
            )

        if not self.inferred:
            raise ValueError(
                "SemanticCandidate represents an inference and must be inferred."
            )
