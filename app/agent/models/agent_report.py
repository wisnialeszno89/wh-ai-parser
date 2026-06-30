from dataclasses import dataclass, field

from app.construction.construction_plan import (
    ConstructionPlan
)


@dataclass
class AgentReport:

    success: bool

    construction_plan: ConstructionPlan

    completed_positions: int = 0

    review_positions: list[int] = field(
        default_factory=list
    )

    messages: list[str] = field(
        default_factory=list
    )