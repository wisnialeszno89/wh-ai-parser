from dataclasses import dataclass

from app.gui.gui_action import (
    GuiAction,
)

from app.runtime.execution.keyboard.keyboard_controller import (
    KeyboardController,
)


@dataclass(slots=True)
class HandlerContext:

    keyboard: KeyboardController

    action: GuiAction