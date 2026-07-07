from dataclasses import dataclass, field


@dataclass
class WorldState:

    screenshot = None

    objects: list = field(

        default_factory=list

    )

    active_tool: str | None = None

    dialogs: list = field(

        default_factory=list

    )

    toolbar_visible: bool = True