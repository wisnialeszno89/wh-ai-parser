from dataclasses import dataclass, field

from app.construction.workflow.workflow_step import (
    WorkflowStep
)


@dataclass
class Workflow:

    steps: list[WorkflowStep] = field(
        default_factory=list
    )