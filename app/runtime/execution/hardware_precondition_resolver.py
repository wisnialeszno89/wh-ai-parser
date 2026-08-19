from __future__ import annotations

from dataclasses import dataclass

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


@dataclass(frozen=True)
class HardwarePreconditionResult:
    ready: bool
    reason: str
    selected_point: tuple[int, int] | None = None


class HardwarePreconditionResolver:
    """Prepare/validate the GUI state required before HARDWARE can be clicked."""

    def __init__(self, context) -> None:
        self.context = context
        self.native = NativeToolbarResolver()

    def inspect(self) -> HardwarePreconditionResult:
        window = getattr(self.context, "window", None)
        if window is None:
            return HardwarePreconditionResult(False, "Window origin unavailable")

        try:
            element = self.native.resolve(
                GuiTool.HARDWARE,
                window.left,
                window.top,
            )
            return HardwarePreconditionResult(
                True,
                "HARDWARE enabled",
                (element.x + element.width // 2, element.y + element.height // 2),
            )
        except RuntimeError as exc:
            return HardwarePreconditionResult(False, str(exc))
