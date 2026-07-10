from __future__ import annotations

from dataclasses import dataclass, field

from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)


@dataclass(slots=True)
class SceneGraph:
    """
    Hierarchical representation of everything
    visible on the screen.
    """

    root: GUIObject

    def walk(self):

        yield from self._walk(self.root)

    def _walk(
        self,
        node: GUIObject,
    ):

        yield node

        for child in node.children:

            yield from self._walk(child)