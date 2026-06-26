from dataclasses import (
    dataclass
)


@dataclass
class ProjectOutcome:

    project_name: str

    success: bool

    execution_time_seconds: float = 0.0

    error_count: int = 0