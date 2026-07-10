from dataclasses import dataclass


@dataclass(slots=True)
class WindowRect:

    left: int

    top: int

    width: int

    height: int