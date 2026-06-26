from dataclasses import (
    dataclass
)


@dataclass
class ReflectionPattern:

    goal_name: str

    successes: int = 0

    failures: int = 0