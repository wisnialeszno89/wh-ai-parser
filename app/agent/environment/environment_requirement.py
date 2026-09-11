from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentRequirement:
    """
    Describes the environment conditions required before
    the agent may safely begin a task or action.

    Requirements intentionally describe the desired state,
    not how that state should be achieved.
    """

    application: str | None = None

    window_title: str | None = None

    requires_focus: bool = False
