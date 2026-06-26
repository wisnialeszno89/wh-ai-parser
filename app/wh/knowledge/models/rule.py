from dataclasses import dataclass


@dataclass(slots=True)
class Rule:

    name: str

    priority: int

    conditions: dict

    actions: dict