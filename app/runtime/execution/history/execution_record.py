from dataclasses import dataclass

from app.gui.enums.gui_tool import (
    GuiTool,
)


@dataclass(slots=True)
class ExecutionRecord:

    tool: GuiTool

    success: bool

    confidence: float

    duration_ms: int

    message: str