from app.runtime.execution.target.target import Target

from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)


class TargetResolver:
    """
    Resolves the best click point for a GUI object.
    """

    def resolve(
        self,
        obj: GUIObject,
    ) -> Target:

        rect = obj.bounds

        return Target(

            x=rect.center[0],

            y=rect.center[1],

        )