from dataclasses import dataclass


@dataclass
class RuntimeEvent:

    name: str

    payload: object | None = None