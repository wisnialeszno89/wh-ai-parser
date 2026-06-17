from dataclasses import dataclass, field
from typing import List

from app.ui.models.ui_object import (
    UIObject
)


@dataclass
class UISceneGraph:

    objects: List[UIObject] = field(
        default_factory=list
    )