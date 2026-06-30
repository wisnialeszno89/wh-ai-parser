from dataclasses import dataclass, field


@dataclass
class OpeningDefinition:

    code: str

    aliases: list[str] = field(
        default_factory=list
    )

    opening_type: str = ""

    direction: str = ""