from dataclasses import (
    dataclass,
    field
)

from app.wh.runtime.vision.goal_execution_result import (
    GoalExecutionResult
)


@dataclass
class TaskExecutionResult:

    task_name: str

    goal_results: list[
        GoalExecutionResult
    ] = field(

        default_factory=list

    )