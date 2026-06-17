from dataclasses import dataclass
from typing import Optional


@dataclass
class UIObject:

    id: str

    object_type: str

    x: int
    y: int

    width: int
    height: int

    label: Optional[str] = None

    selected: bool = False