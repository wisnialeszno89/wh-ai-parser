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

from app.runtime.execution.vision.models.scene_graph import (
    SceneGraph,
)

from app.wh.vision.screenshot import (
    Screenshot,
)


class SceneGraphBuilder:

    def build(
        self,
        screenshot: Screenshot,
    ) -> SceneGraph:

        root = GUIObject(

            id="window",

            type=ControlType.WINDOW,

            role=ControlRole.UNKNOWN,

            state=ControlState.VISIBLE,

            bounds=Rect(

                x=0,

                y=0,

                width=screenshot.width,

                height=screenshot.height,

            ),
        )

        return SceneGraph(
            root=root,
        )