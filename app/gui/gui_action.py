from dataclasses import dataclass
from typing import Any

from app.gui.enums.gui_tool import (
    GuiTool
)


@dataclass
class GuiAction:

    tool: GuiTool

    payload: Any = None