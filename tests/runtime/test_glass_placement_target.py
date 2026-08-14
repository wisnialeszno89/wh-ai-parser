from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor


def test_glass_uses_selected_frame_point():
    executor = object.__new__(ActionExecutor)
    executor.context = SimpleNamespace(
        gui_state=SimpleNamespace(
            last_selected_point=(120, 240),
        )
    )

    action = SimpleNamespace(
        tool=GuiTool.GLASS,
        intent=GuiIntent.CREATE,
    )

    assert executor._resolve_create_point(
        action,
        vision=None,
    ) == (120, 240)
