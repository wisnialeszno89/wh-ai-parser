from enum import Enum


class EnvironmentReadiness(str, Enum):
    """
    High-level readiness state of the current environment.
    """

    READY = "ready"

    PREPARATION_REQUIRED = (
        "preparation_required"
    )

    MANUAL_INTERVENTION_REQUIRED = (
        "manual_intervention_required"
    )
