from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeInteraction:

    type: str

    value: str | None = None