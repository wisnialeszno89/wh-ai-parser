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


class SectionAnalyzer:
    """
    Splits the toolbar into logical sections.

    MVP:
    Sections are currently distributed evenly across
    the toolbar.

    In Vision V2 this analyzer will detect real
    section boundaries directly from the screenshot.
    """

    SECTION_ROLES = [

        ControlRole.FRAME_SECTION,

        ControlRole.GLASS_SECTION,

        ControlRole.HARDWARE_SECTION,

        ControlRole.DIMENSIONS_SECTION,

        ControlRole.COLOR_SECTION,

        ControlRole.ACCESSORIES_SECTION,

    ]

    def analyze(
        self,
        screenshot: Screenshot,
        toolbar: GUIObject,
    ) -> None:

        toolbar.children.clear()

        section_width = (

            toolbar.bounds.width //

            len(self.SECTION_ROLES)

        )

        for index, role in enumerate(

            self.SECTION_ROLES

        ):

            section = GUIObject(

                id=role.value,

                type=ControlType.SECTION,

                role=role,

                state=ControlState.VISIBLE,

                bounds=Rect(

                    x=index * section_width,

                    y=toolbar.bounds.y,

                    width=section_width,

                    height=toolbar.bounds.height,

                ),

            )

            toolbar.add_child(

                section

            )