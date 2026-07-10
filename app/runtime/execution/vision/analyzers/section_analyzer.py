from app.runtime.execution.vision.models.control_role import ControlRole
from app.runtime.execution.vision.models.control_state import ControlState
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.rect import Rect
from app.wh.vision.screenshot import Screenshot


class SectionAnalyzer:
    """
    Splits the toolbar into logical sections.

    MVP:
    Currently uses fixed-width sections.
    Later this analyzer will detect real separators
    from the screenshot.
    """

    SECTION_COUNT = 6

    def analyze(
        self,
        screenshot: Screenshot,
        toolbar: GUIObject,
    ) -> None:

        section_width = (
            toolbar.bounds.width // self.SECTION_COUNT
        )

        toolbar.children.clear()

        for index in range(self.SECTION_COUNT):

            section = GUIObject(
                id=f"section_{index + 1}",
                type=ControlType.SECTION,
                role=ControlRole.UNKNOWN,
                state=ControlState.VISIBLE,
                bounds=Rect(
                    x=index * section_width,
                    y=toolbar.bounds.y,
                    width=section_width,
                    height=toolbar.bounds.height,
                ),
            )

            toolbar.add_child(section)