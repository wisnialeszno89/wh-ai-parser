from dataclasses import (
    dataclass
)


@dataclass
class ProjectAnalytics:

    total_projects: int

    successful_projects: int

    failed_projects: int

    success_rate: float

    average_execution_time: float

    average_error_count: float