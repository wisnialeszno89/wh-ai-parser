from dataclasses import dataclass


@dataclass
class Glass:

    ug: float | None = None

    panes: int | None = None