from dataclasses import dataclass, field
from typing import List

from app.core.scene.models.scene_object import (
    SceneObject
)

from app.core.scene.models.scene_relation import (
    SceneRelation
)

from app.core.scene.models.selection_state import (
    SelectionState
)


@dataclass
class SceneGraph:

    objects: List[SceneObject] = field(
        default_factory=list
    )

    relations: List[SceneRelation] = field(
        default_factory=list
    )

    selection_state: SelectionState = field(
        default_factory=SelectionState
    )

    available_actions: List[str] = field(
        default_factory=list
    )