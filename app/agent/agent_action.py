from dataclasses import dataclass

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)


@dataclass(frozen=True)
class AgentAction:
    """
    A semantic action planned by the agent.

    This intentionally does NOT contain GUI clicks or screen
    coordinates. Optional target/value fields carry semantic
    intent between the reasoner and the local executor.
    """

    name: str

    description: str

    target: str | None = None

    value: str | None = None

    requires_confirmation: bool = False

    environment_requirement: (
        EnvironmentRequirement | None
    ) = None
