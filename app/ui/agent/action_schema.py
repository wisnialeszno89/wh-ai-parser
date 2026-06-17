from dataclasses import dataclass


@dataclass
class Action:

    action: str

    params: dict