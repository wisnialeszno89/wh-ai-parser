from pathlib import Path
from types import SimpleNamespace as NS

import cv2
import numpy as np
import pytest
from PIL import Image

from app.agent.learning.windowhub_offer_editor import (
    find_drawing, fixed_window_stage, selected_row_box, selected_window_matches, toolbar_tool,
)
from app.gui.enums.gui_tool import GuiTool
from tools import run_windowhub_autonomous_offer as live
from tools.check_windowhub_builder_sequence import ARCHIVED_TEMPLATES, TOOLBAR_CROP

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "research/datasets/windowhub/builder_region/raw"


def frame(filename):
    return cv2.cvtColor(cv2.imread(str(FIXTURES / filename)), cv2.COLOR_BGR2RGB)


@pytest.mark.parametrize(("filename", "expected"), [
    ("builder_01_empty.png", "empty"),
    ("builder_02_frame.png.png", "frame"),
    ("builder_03_frame_sash.png.png", "unknown"),
    ("builder_04_frame_sash_glass.png.png", "unknown"),
])
def test_offer_editor_observes_archive_without_absolute_canvas_coordinates(filename, expected):
    rgb = frame(filename)
    for image in (rgb, np.pad(rgb, ((22, 0), (33, 0), (0, 0)), constant_values=235)):
        row = selected_row_box(image)
        assert row is not None
        drawing = find_drawing(image, row)
        assert drawing is not None and drawing.y > row.bottom
        assert fixed_window_stage(drawing.crop(image)) == expected


def test_one_fixed_glass_panel_is_not_two_or_a_sash():
    rgb = frame("builder_02_frame.png.png")
    drawing = find_drawing(rgb, selected_row_box(rgb))
    crop = drawing.crop(rgb).copy()
    white = (crop > 249).all(axis=2)
    crop[white] = (0, 224, 255)
    assert fixed_window_stage(crop) == "fixed_glazed"
    crop[:, 132:142] = (0, 255, 0)
    assert fixed_window_stage(crop) == "unknown"


@pytest.mark.parametrize(("file", "tool", "expected_y"), [
    ("builder_01_empty.png", GuiTool.FRAME, 421),
    ("builder_02_frame.png.png", GuiTool.GLASS, 539),
])
def test_locates_frame_and_glass_from_actual_toolbar(file, tool, expected_y):
    source = Image.fromarray(frame(file))
    path, scale = ARCHIVED_TEMPLATES[tool]
    with Image.open(ROOT / "templates" / path) as target:
        template = target.convert("L").resize(
            (round(target.width * scale), round(target.height * scale)), Image.Resampling.BILINEAR,
        )
    result = toolbar_tool(np.asarray(source.convert("L").crop(TOOLBAR_CROP)), np.asarray(template))
    assert result is not None and abs(result[1] - expected_y) <= 3


def test_selected_row_must_be_same_number_quantity_type_and_size():
    lines = [
        NS(label=label, confidence=0.96, bounds=(pos, 0, pos + 1, 1))
        for pos, label in enumerate(["2", "1", "Okno", "0,00", "1100 × 1000"])
    ]
    assert selected_window_matches(lines, 2, 1100, 1000)
    assert not selected_window_matches(lines, 1, 1100, 1000)
    assert not selected_window_matches(lines, 2, 1000, 1000)
    lines[1].label = "7"
    assert not selected_window_matches(lines, 2, 1100, 1000)


def test_build_reobserves_after_each_click_and_verifies_fixed_glass(monkeypatch):
    scene = NS(observation=NS(metadata={"window_handle": 200}))
    draw = NS(center=(95, 95))
    observations = iter((scene, None, None, draw, state) for state in ("empty", "empty", "frame", "frame", "fixed_glazed"))
    clicks = []
    tools = []
    monkeypatch.setattr(live, "observe_workspace", lambda *a: next(observations))
    def locate(image, rect, hwnd, tool):
        tools.append(tool)
        return 216, (5, len(tools))

    monkeypatch.setattr(live, "tool_target", locate)
    monkeypatch.setattr(live, "click_owned", lambda *a, **kw: clicks.append((a[-1], kw.get("toolbar"))))
    assert live.build_fixed(object(), "OFR/42-", object(), 1, (1000, 1000)) is scene
    assert tools == [GuiTool.FRAME, GuiTool.GLASS]
    assert clicks == [((5, 1), 216), ((95, 95), None), ((5, 2), 216), ((95, 95), None)]


def test_changed_selection_after_tool_blocks_placement(monkeypatch):
    scene = NS(observation=NS(metadata={"window_handle": 200}))
    workspace = (scene, None, None, NS(center=(95, 95)), "empty")
    calls = []

    def observe(*args):
        if not calls:
            return workspace
        raise live.WorkspaceBlocked("selected_window_number_quantity_or_dimensions_unverified")

    monkeypatch.setattr(live, "observe_workspace", observe)
    monkeypatch.setattr(live, "tool_target", lambda *a: (216, (5, 20)))
    monkeypatch.setattr(live, "click_owned", lambda *a, **kw: calls.append(kw["toolbar"]))
    with pytest.raises(live.WorkspaceBlocked, match="selected_window"):
        live.build_fixed(object(), "OFR/42-", object(), 1, (1000, 1000))
    assert calls == [216]


def test_same_hwnd_with_changed_native_offer_is_rejected(monkeypatch):
    monkeypatch.setattr(live, "belongs_to_offer", lambda *args: True)
    scene = NS(observation=NS(metadata={"window_handle": 200}))
    api = NS(title=lambda hwnd: "Okna - OFR/43-")
    assert not live.owns_native_workspace(scene, "OFR/42-", api)


def test_offer_runs_both_wizards_and_both_builds_in_one_same_offer(monkeypatch):
    calls = []
    wizard = object()
    monkeypatch.setattr(live, "inspect", lambda loop: object())
    monkeypatch.setattr(live, "open_next", lambda *args: calls.append(("add_next", args[2])) or wizard)
    monkeypatch.setattr(live, "owned_discount", lambda *args: False)
    monkeypatch.setattr(live, "stage_of", lambda scene: "position")
    monkeypatch.setattr(live, "belongs_to_offer", lambda *args: True)
    monkeypatch.setattr(live, "run", lambda loop, offer, api, **kw: calls.append((
        "wizard", offer, kw["width"], kw["height"],
    )) or 0)
    monkeypatch.setattr(live, "build_fixed", lambda loop, offer, api, number, size: calls.append((
        "build", offer, number, size,
    )))
    assert live.run_offer(object(), "OFR/42-", object(), live.POSITIONS) == 0
    assert calls == [
        ("wizard", "OFR/42-", 1000, 1000),
        ("build", "OFR/42-", 1, (1000, 1000)),
        ("add_next", "OFR/42-"),
        ("wizard", "OFR/42-", 1100, 1000),
        ("build", "OFR/42-", 2, (1100, 1000)),
    ]


def test_sash_builder_consumes_archived_visual_decisions_and_verifies_marker(monkeypatch, capsys):
    from tools.check_windowhub_opening_markers import CANVAS_CROP
    from app.agent.learning.windowhub_builder_replay import read_builder_stage
    from app.agent.learning.windowhub_offer_editor import Box

    paths = sorted(FIXTURES.glob("builder_*.png"))
    x, y, right, bottom = CANVAS_CROP
    drawing = Box(x, y, right - x, bottom - y)
    scene = NS(observation=NS(metadata={"window_handle": 200}))
    frames = []
    for path in paths:
        rgb = frame(path.name)
        frames.append((scene, None, rgb, drawing, read_builder_stage(drawing.crop(rgb))))

    # One new observation after each toolbar selection and each placement.
    observations = iter([frames[0], *[f for pair in zip(frames, frames[1:]) for f in pair]])
    actions = []

    def locate(rgb, rect, hwnd, tool):
        actions.append(tool.name)
        return 216, (5, 20)

    monkeypatch.setattr(live, "observe_workspace", lambda *args, **kwargs: next(observations))
    monkeypatch.setattr(live, "active_mdi_child", lambda hwnd, api: 14)
    monkeypatch.setattr(live, "tool_target", locate)
    monkeypatch.setattr(live, "click_owned", lambda *args, **kwargs: None)
    monkeypatch.setattr(live, "apply_ur_hardware", lambda loop, api, hwnd, child: actions.append((hwnd, child)))
    assert live.build_construction(object(), "OFR/42-", object(), 1, (1000, 1000), opening=True) is scene
    assert actions == ["FRAME", "SASH", "GLASS", "HARDWARE", (200, 14)]
    assert "WH_AUTONOMOUS_OPENING_MARKER=RIGHT" in capsys.readouterr().out


def test_hardware_requires_catalog_ur_choice():
    from app.agent.runtime.windowhub_hardware_dialog import choose_ur_option

    standard = ("UR ACTIVPILOT", False, object())
    configured = ("UR 8", True, object())
    assert choose_ur_option([standard, configured]) is configured
    assert choose_ur_option([standard, ("UR 8", False, object())]) is standard
    assert choose_ur_option([("U 1", True, object()), ("Bez okuć", True, object())]) is None
    assert choose_ur_option([("UR 2", False, object()), ("UR 8", False, object())]) is None
