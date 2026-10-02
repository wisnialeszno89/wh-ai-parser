from dataclasses import dataclass

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)


@dataclass(frozen=True)
class AgentAction:
    """
    A semantic action planned by the agent.

    This intentionally does NOT contain GUI clicks.
    GUI/runtime execution will later translate semantic actions
    into controlled executor commands.
    """

    name: str

    description: str

    requires_confirmation: bool = False

    environment_requirement: (
        EnvironmentRequirement | None
    ) = None

    # Optional semantic target carried by the plan. This is a label or
    # other semantic identifier, never a coordinate or low-level command.
    target: str | None = None

    # Optional semantic text value for safe field-entry actions.
    value: str | None = None

    # Pure workflow/business actions can execute without another expensive
    # environment observe → perceive cycle. GUI actions set this flag or
    # are recognized explicitly by the control loop.
    requires_environment_observation: bool = False
