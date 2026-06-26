from dataclasses import (
    dataclass,
    field
)


@dataclass
class ProjectExecutionReport:

    completed_goals: list = field(

        default_factory=list

    )

    failed_goals: list = field(

        default_factory=list

    )

    warnings: list = field(

        default_factory=list

    )

    requires_human_review: bool = False

    success_rate: float = 100.0