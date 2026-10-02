from dataclasses import dataclass


@dataclass(frozen=True)
class PlanReplanRecord:
    """
    Records one plan replacement triggered by failed
    verification.
    """

    failed_action_name: str

    reason: str

    attempts: int

    replacement_actions: tuple[str, ...]
