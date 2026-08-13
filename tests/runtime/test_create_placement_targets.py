from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor


def _executor_with_selected_point(point):
    executor = object.__new__(ActionExecutor)
    executor.context = SimpleNamespace(
        gui_state=SimpleNamespace(
            last_selected_point=point,
        )
    )
    return executor


def test_sash_uses_selected_frame_point():
    executor = _executor_with_selected_point((120, 240))

    action = GuiAction(
        tool=GuiTool.SASH,
        intent=GuiIntent.CREATE,
    )

    assert executor._resolve_create_point(
        action,
        vision=None,
    ) == (120, 240)


def test_frame_falls_back_to_canvas_resolver():
    executor = _executor_with_selected_point(None)

    executor.canvas = SimpleNamespace(
        resolve=lambda vision: (70, 80),
    )

    action = GuiAction(
        tool=GuiTool.FRAME,
        intent=GuiIntent.CREATE,
    )

    assert executor._resolve_create_point(
        action,
        vision=object(),
    ) == (70, 80)
