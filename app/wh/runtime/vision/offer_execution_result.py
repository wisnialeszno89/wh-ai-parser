from dataclasses import (
    dataclass,
    field
)

from app.wh.runtime.vision.task_execution_result import (
    TaskExecutionResult
)


@dataclass
class OfferExecutionResult:

    task_results: list[
        TaskExecutionResult
    ] = field(

        default_factory=list

    )