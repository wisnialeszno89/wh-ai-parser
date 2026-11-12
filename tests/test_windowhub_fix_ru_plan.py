import pytest

from app.agent.offers.windowhub_fix_ru_plan import plan_fix_ru
from app.gui.enums.gui_tool import GuiTool
from app.window_model.topology import WindowSide

EXAMPLE = dict(width_mm=1600, height_mm=1400, layout="FIX+RU", split_from_left_mm=650, opening_code="DKL")


@pytest.mark.parametrize(("layout", "fixed", "moving"), [
    ("FIX+RU", WindowSide.LEFT, WindowSide.RIGHT),
    ("RU+FIX", WindowSide.RIGHT, WindowSide.LEFT),
])
def test_explicit_split_targets_fixed_glass_and_ru_hardware_separately(layout, fixed, moving):
    steps = plan_fix_ru(**(EXAMPLE | {"layout": layout}))
    assert [step.gui_tool for step in steps] == [
        GuiTool.FRAME, GuiTool.MULLION, GuiTool.SASH, GuiTool.GLASS, GuiTool.GLASS, GuiTool.HARDWARE,
    ]
    frame, mullion, sash, _, _, hardware = steps
    assert frame.properties == {"width_mm": 1600, "height_mm": 1400}
    assert mullion.properties["offset_from_left_mm"] == 650
    assert sash.side == hardware.side == moving
    assert hardware.parent_id == sash.element_id
    assert hardware.properties["direction"] == "LEFT"
    glass = {step.side: step for step in steps if step.gui_tool == GuiTool.GLASS}
    assert glass[fixed].parent_id == frame.element_id
    assert glass[moving].parent_id == sash.element_id
    assert glass[WindowSide.LEFT].properties["field_width_mm"] == 650
    assert glass[WindowSide.RIGHT].properties["field_width_mm"] == 950


@pytest.mark.parametrize(("change", "message"), [
    ({"split_from_left_mm": None}, "Brakuje wymiaru podziału"),
    ({"split_from_left_mm": 1600}, "pomiędzy"),
    ({"opening_code": None}, "kierunek"),
    ({"layout": ""}, "kolejność pól"),
])
def test_incomplete_or_invalid_requests_require_review(change, message):
    with pytest.raises(ValueError, match=message):
        plan_fix_ru(**(EXAMPLE | change))
