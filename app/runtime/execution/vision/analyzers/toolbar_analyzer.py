from app.runtime.execution.vision.models.control_role import ControlRole
from app.runtime.execution.vision.models.control_state import ControlState
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.rect import Rect
from app.wh.vision.screenshot import Screenshot


class ToolbarAnalyzer:

    TOOLBAR_HEIGHT = 135

    def analyze(
        self,
        screenshot: Screenshot,
    ) -> GUIObject:

        return GUIObject(
            id="toolbar",
            type=ControlType.TOOLBAR,
            role=ControlRole.UNKNOWN,
            state=ControlState.VISIBLE,
            bounds=Rect(
                x=0,
                y=0,
                width=screenshot.width,
                height=self.TOOLBAR_HEIGHT,
            ),
        )