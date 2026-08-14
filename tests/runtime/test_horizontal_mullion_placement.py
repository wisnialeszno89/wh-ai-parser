from types import SimpleNamespace

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.vision.models.rect import Rect


def _executor_with_state():
    executor = ActionExecutor.__new__(ActionExecutor)
    executor.context = SimpleNamespace(
        gui_state=SimpleNamespace(
            mullion_point=(160, 150),
            mullion_orientation="horizontal",
            workspace_bounds=(80, 100, 160, 100),
            panel_side="top",
            panel_pair_point=None,
            last_panel_component=None,
            last_selected_point=None,
        )
    )
    return executor


def test_horizontal_mullion_uses_top_cell_for_sash():
    executor = _executor_with_state()

    point = executor._resolve_panel_point(
        vision=None,
        tool=GuiTool.SASH,
    )

    assert point == (160, 125)


def test_horizontal_mullion_moves_to_bottom_cell_after_glass():
    executor = _executor_with_state()
    executor.context.gui_state.panel_pair_point = (160, 125)
    executor.context.gui_state.last_panel_component = "GLASS"

    executor._advance_panel_after_glass()

    assert executor.context.gui_state.panel_side == "bottom"
    assert executor.context.gui_state.panel_pair_point is None

    point = executor._resolve_panel_point(
        vision=None,
        tool=GuiTool.SASH,
    )

    assert point == (160, 175)
