from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    """
    A named area of competence available to the agent.

    Capabilities describe WHAT the agent is able to handle.
    They do not contain execution logic.
    """

    name: str
    description: str
