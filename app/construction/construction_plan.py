from dataclasses import dataclass, field

from app.construction.construction_step import (
    ConstructionStep
)


@dataclass
class ConstructionPlan:

    steps: list[ConstructionStep] = field(
        default_factory=list
    )

    confidence: float = 1.0

    from dataclasses import dataclass, field

from app.construction.construction_step import (
    ConstructionStep
)

from app.construction.enums.plan_decision import (
    PlanDecision
)


@dataclass

class ConstructionPlan:

    steps: list[ConstructionStep] = field(
        default_factory=list
    )

    confidence: float = 1.0

    decision: PlanDecision = (
        PlanDecision.AUTO
    )