from dataclasses import dataclass, field


@dataclass
class ConstructionDefinition:

    code: str

    fields: list[str] = field(
        default_factory=list
    )