from dataclasses import dataclass


@dataclass(frozen=True)
class ReasoningAction:
    """
    Safe semantic action proposal produced by a reasoning provider.

    The reasoning layer intentionally cannot provide:
    - coordinates
    - mouse commands
    - keyboard commands
    - executor names
    - low-level GUI instructions

    The runtime converts this semantic proposal into AgentAction
    and routes it through the existing execution/safety boundary.
    """

    name: str

    description: str

    requires_confirmation: bool = False
