from dataclasses import dataclass


@dataclass(slots=True)
class MissingInformationItem:

    field: str

    priority: int

    question: str