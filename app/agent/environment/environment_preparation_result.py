from dataclasses import dataclass, field


@dataclass(frozen=True)
class EnvironmentPreparationResult:
    """
    Result of executing an environment preparation step.

    The result describes whether the requested preparation
    operation was successfully performed.

    Actual environment readiness must still be verified by
    observing the environment again.
    """

    success: bool

    reason: str = ""

    requires_user_action: bool = False

    metadata: dict[str, object] = field(
        default_factory=dict
    )
