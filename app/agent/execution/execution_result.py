from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionResult:
    """
    Result returned after executing one semantic action.

    ExecutionResult intentionally contains no UI-specific
    information. GUI implementations can later add details
    through metadata.
    """

    action_name: str

    success: bool

    message: str

    requires_manual_review: bool = False

    metadata: dict[str, object] | None = None
