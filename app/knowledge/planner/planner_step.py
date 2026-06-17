from dataclasses import dataclass


@dataclass
class PlannerStep:

    action: str

    params: dict