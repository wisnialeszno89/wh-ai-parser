from dataclasses import (
    dataclass
)


@dataclass
class GoalReflection:

    goal_name: str

    success: bool

    conclusion: str