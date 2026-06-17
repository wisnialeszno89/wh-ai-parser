from dataclasses import dataclass
from typing import Optional


@dataclass
class SceneObject:

    id: str

    object_type: str

    x: int
    y: int

    width: int
    height: int

    selected: bool = False

    label: Optional[str] = None

    orientation: Optional[str] = None