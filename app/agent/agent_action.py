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
