from dataclasses import dataclass


@dataclass(slots=True)
class ActionMemory:

    attempts: int = 0

    successes: int = 0

    failures: int = 0

    recoveries: int = 0