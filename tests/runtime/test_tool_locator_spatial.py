from types import SimpleNamespace

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.tool_locator import ToolLocator


def _locator():
    return object.__new__(ToolLocator)


def _reference():
    return SimpleNamespace(
        name="frame_tool.png",
        x=8,
        y=620,
        width=32,
        height=32,
        confidence=0.90,
    )


def test_top_toolbar_false_positive_is_rejected():
    locator = _locator()
    screenshot = SimpleNamespace(shape=(1000, 1400, 3))

    top_toolbar = SimpleNamespace(
        name="sash_tool.png",
        x=580,
        y=15,
        width=32,
        height=32,
        confidence=0.62,
    )

    assert locator._same_construction_column(
        _reference(),
        top_toolbar,
        screenshot,
    ) is False


def test_side_construction_icon_is_accepted():
    locator = _locator()
    screenshot = SimpleNamespace(shape=(1000, 1400, 3))

    left_panel = SimpleNamespace(
        name="sash_tool.png",
        x=8,
        y=665,
        width=32,
        height=32,
        confidence=0.51,
    )

    assert locator._same_construction_column(
        _reference(),
        left_panel,
        screenshot,
    ) is True


def test_construction_column_is_position_relative():
    locator = _locator()
    screenshot = SimpleNamespace(shape=(1000, 1400, 3))

    reference_a = _reference()
    icon_a = SimpleNamespace(
        name="sash_tool.png",
        x=10,
        y=690,
        width=28,
        height=28,
        confidence=0.50,
    )

    reference_b = SimpleNamespace(
        name="frame_tool.png",
        x=438,
        y=280,
        width=32,
        height=32,
        confidence=0.90,
    )
    icon_b = SimpleNamespace(
        name="sash_tool.png",
        x=440,
        y=330,
        width=28,
        height=28,
        confidence=0.50,
    )

    assert locator._same_construction_column(
        reference_a,
        icon_a,
        screenshot,
    ) is True
    assert locator._same_construction_column(
        reference_b,
        icon_b,
        screenshot,
    ) is True
    assert GuiTool.SASH.name == "SASH"
