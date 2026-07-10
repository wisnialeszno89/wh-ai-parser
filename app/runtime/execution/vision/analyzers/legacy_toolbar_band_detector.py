from app.ui.runtime.find_toolbar_band import (
    find_toolbar_band,
)

from app.runtime.execution.vision.models.control_role import (
    ControlRole,
)

from app.runtime.execution.vision.models.control_state import (
    ControlState,
)

from app.runtime.execution.vision.models.control_type import (
    ControlType,
)

from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)

from app.runtime.execution.vision.models.rect import (
    Rect,
)

from app.wh.vision.screenshot import (
    Screenshot,
)


class LegacyToolbarBandDetector:
    """
    Adapter between the legacy toolbar finder and
    the new Vision Engine.
    """

    def analyze(
        self,
        screenshot: Screenshot,
    ) -> GUIObject | None:

        regions = find_toolbar_band(
            screenshot.image,
        )

        if not regions:
            return None

        region = regions[0]

        return GUIObject(
            id="toolbar",
            type=ControlType.TOOLBAR,
            role=ControlRole.UNKNOWN,
            state=ControlState.VISIBLE,
            bounds=Rect(
                x=region["x"],
                y=region["y"],
                width=region["width"],
                height=region["height"],
            ),
        )