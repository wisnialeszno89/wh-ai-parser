from dataclasses import dataclass, field


@dataclass
class WorkflowDefinition:

    name: str

    difficulty: str

    manual_review: bool

    steps: list = field(
        default_factory=list
    )