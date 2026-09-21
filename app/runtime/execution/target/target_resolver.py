from app.runtime.execution.target.target import Target
from app.runtime.execution.vision.models.gui_object import GUIObject


class TargetResolver:
    """
    Resolves a safe interaction point from a perceived GUI object.
    """

    def resolve(self, obj: GUIObject) -> Target:
        if obj.bounds is None:
            raise ValueError(
                f"Cannot resolve target for GUI object without bounds: {obj.id}"
            )

        x, y = obj.bounds.center

        return Target(
            x=x,
            y=y,
        )
