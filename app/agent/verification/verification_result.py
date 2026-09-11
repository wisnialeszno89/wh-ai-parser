from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerificationResult:
    """
    Result of comparing an expected outcome with the
    currently perceived environment.
    """

    verified: bool

    reason: str

    confidence: float = 1.0

    metadata: dict[str, object] = field(
        default_factory=dict
    )
