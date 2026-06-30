from dataclasses import dataclass, field


@dataclass
class OpeningDefinition:

    code: str

    aliases: list[str] = field(
        default_factory=list
    )

    opening: str = ""

    direction: str = ""

    requires_frame: bool = True

    requires_sash: bool = True

    requires_hardware: bool = True

    requires_handle: bool = True

    requires_glass: bool = True

    workflow: str = ""

    difficulty: str = "easy"