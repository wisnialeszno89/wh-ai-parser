from dataclasses import dataclass

from app.knowledge.planner.planner_step import (
    PlannerStep
)


@dataclass
class PlannerResult:

    steps: list[
        PlannerStep
    ]