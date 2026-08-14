from types import SimpleNamespace

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.tool_locator import ToolLocator
from app.runtime.execution.vision.models.rect import Rect


def _locator():
    return object.__new__(ToolLocator)


def _vision(canvas):
    return SimpleNamespace(
        canvas=SimpleNamespace(bounds=canvas),
    )


def test_top_toolbar_false_positive_is_rejected():
    locator = _locator()
    canvas = Rect(x=90, y=600, width=240, height=170)

    top_toolbar = SimpleNamespace(
        name="sash_tool.png",
        x=580,
        y=15,
        width=32,
        height=32,
        confidence=0.62,
    )

    assert locator._panel_candidates(
        _vision(canvas),
        [top_toolbar],
    ) == []


def test_side_construction_icon_is_accepted():
    locator = _locator()
    canvas = Rect(x=90, y=600, width=240, height=170)

    left_panel = SimpleNamespace(
        name="sash_tool.png",
        x=8,
        y=650,
        width=32,
        height=32,
        confidence=0.51,
    )

    candidates = locator._panel_candidates(
        _vision(canvas),
        [left_panel],
    )

    assert candidates == [left_panel]


def test_workspace_anchor_does_not_depend_on_absolute_screen_position():
    locator = _locator()

    canvas_a = Rect(x=90, y=600, width=240, height=170)
    icon_a = SimpleNamespace(
        name="sash_tool.png", x=8, y=650, width=32, height=32, confidence=0.50
    )

    canvas_b = Rect(x=520, y=240, width=240, height=170)
    icon_b = SimpleNamespace(
        name="sash_tool.png", x=438, y=290, width=32, height=32, confidence=0.50
    )

    assert locator._panel_candidates(_vision(canvas_a), [icon_a]) == [icon_a]
    assert locator._panel_candidates(_vision(canvas_b), [icon_b]) == [icon_b]

    assert GuiTool.SASH.name == "SASH"
