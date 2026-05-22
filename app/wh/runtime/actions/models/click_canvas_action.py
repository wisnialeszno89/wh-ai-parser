from dataclasses import dataclass

from app.wh.runtime.canvas_target import (
    CanvasTarget
)

from app.wh.runtime.actions.models.runtime_action import (
    RuntimeAction
)


@dataclass
class ClickCanvasAction(RuntimeAction):

    target: CanvasTarget

    def __init__(

        self,
        target: CanvasTarget
    ):

        super().__init__(
            type="click_canvas"
        )

        self.target = target