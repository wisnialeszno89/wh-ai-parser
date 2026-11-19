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


def test_editor_transition_uses_real_workspace_image_and_position_readback(monkeypatch, capsys):
    from app.wh.vision import mss_screenshot_engine
    from app.agent.offers import windowhub_customer_visual_selection as ocr

    rgb = frame("builder_01_empty.png")
    rect = NS(width=rgb.shape[1], height=rgb.shape[0])
    scene = NS(observation=NS(metadata={"window_rect": rect}))
    scope = NS(frame=70)
    monkeypatch.setattr(live, "active_mdi_child", lambda *args: 77)
    scope.editor_candidate = lambda *a, **kw: "eligible"
    accepted = []
    scope.accept_visual_editor = lambda *a: not accepted.append(a)
    monkeypatch.setattr(mss_screenshot_engine, "MSSScreenshotEngine", lambda: NS(
        capture=lambda rect: NS(image=rgb[:, :, ::-1]),
    ))
    monkeypatch.setattr(ocr, "_ocr_text_results", lambda *args: [
        NS(label="1 1 Okno 1000 x 1000", confidence=1.0, bounds=(0, 0, 20, 15)),
    ])
    tools = []
    monkeypatch.setattr(live, "tool_target", lambda rgb, rect, hwnd, tool, **kw: tools.append(tool))
    assert not live.verify_editor_transition(scene, scope, object(), 1, (1200, 1000), opening=True)
    assert not accepted
    assert live.verify_editor_transition(scene, scope, object(), 1, (1000, 1000), opening=True)
    assert tools == [GuiTool.FRAME]
    assert accepted
    assert "WH_EDITOR_EVIDENCE=verified_empty" in capsys.readouterr().out


def test_selected_row_at_top_of_tall_grid_still_finds_drawing():
    from app.agent.learning.windowhub_offer_editor import position_grid_bottom

    rgb = frame("builder_01_empty.png")
    row = selected_row_box(rgb)
    drawing = find_drawing(rgb, row)
    height = 300
    insertion = row.bottom + 4
    extension = np.repeat(rgb[insertion:insertion + 1], height, axis=0)
    tall_grid = np.concatenate((rgb[:insertion], extension, rgb[insertion:]))
    observed_row = selected_row_box(tall_grid)
    assert observed_row == row
    bottom_edge = position_grid_bottom(tall_grid.max(axis=2) < 90, row)
    assert bottom_edge is not None and row.bottom + height < bottom_edge < drawing.y + height
    found = find_drawing(tall_grid, row)
    assert found is not None
    assert (found.x, found.y, found.width, found.height) == (
        drawing.x, drawing.y + height, drawing.width, drawing.height,
    )
    assert fixed_window_stage(found.crop(tall_grid)) == "empty"


def test_selected_draft_build_keeps_document_and_checks_dimensions(monkeypatch):
    scope = object()
    calls = []
    monkeypatch.setattr(live, "inspect", lambda loop: object())
    monkeypatch.setattr(live.NewOfferHandoff, "bind_selected_draft", lambda *args: scope)
    monkeypatch.setattr(live, "verify_editor_transition", lambda scene, offer, api, num, size, **kw: (
        calls.append(("observe", offer, num, size, kw["opening"])) or True
    ))
    monkeypatch.setattr(live, "build_construction", lambda loop, offer, api, num, size, **kw: (
        calls.append(("build", offer, num, size, kw["opening"]))
    ))
    assert live.build_selected_draft(object(), object(), "Dokument15", (1000, 1000), construction="ur") == 0
    assert calls == [
        ("observe", scope, 1, (1000, 1000), True),
        ("build", scope, 1, (1000, 1000), True),
    ]


def test_wider_drawing_search_recovers_only_a_unique_proportional_outline():
    from app.agent.learning.windowhub_offer_editor import locate_drawing

    rgb = frame("builder_01_empty.png")
    row = selected_row_box(rgb)
    # Move the editor panel down while preserving the grid's lower edge.
    insertion = 372
    gap = np.full((180, rgb.shape[1], 3), 218, dtype=rgb.dtype)
    shifted = np.concatenate((rgb[:insertion], gap, rgb[insertion:]))
    assert find_drawing(shifted, row) is None
    found, diagnosis = locate_drawing(shifted, row, expected_size=(1000, 1000))
    assert found.y == 578
    assert diagnosis["recovered"]
    assert diagnosis["outline_top"] > diagnosis["first_search_end"]
    found, diagnosis = locate_drawing(shifted, row, expected_size=(1500, 1000))
    assert found is None and diagnosis["diagnosis"] == "outline_proportions_disagree"


def test_unverified_effect_is_reobserved_without_replaying_click(monkeypatch, capsys):
    scene = NS(observation=NS(metadata={"window_handle": 200}))
    draw = NS(center=(100, 120))
    empty = (scene, None, None, draw, "empty")
    states = iter([empty] * 7)
    clicks = []
    monkeypatch.setattr(live, "observe_workspace", lambda *a: next(states))
    monkeypatch.setattr(live, "tool_target", lambda *a: (206, (12, 100)))
    monkeypatch.setattr(live, "click_owned", lambda *a, **kw: clicks.append(a[-1]))
    monkeypatch.setattr(live.time, "sleep", lambda *a: None)
    with pytest.raises(live.WorkspaceBlocked, match="construction_effect_unverified:empty"):
        live.build_fixed(object(), "OFR/42-", object(), 1, (1000, 1000))
    assert clicks == [(12, 100), (100, 120)]
    assert '"expected": "frame"' in capsys.readouterr().out


def test_delayed_effect_recovers_and_continues_without_duplicate_click(monkeypatch, capsys):
    scene = NS(observation=NS(metadata={"window_handle": 200}))
    draw = NS(center=(100, 120))
    states = iter((scene, None, None, draw, state) for state in (
        "empty", "empty", "unknown", "frame", "frame", "fixed_glazed",
    ))
    clicks = []
    monkeypatch.setattr(live, "observe_workspace", lambda *a: next(states))
    monkeypatch.setattr(live, "tool_target", lambda *a: (206, (12, 100)))
    monkeypatch.setattr(live, "click_owned", lambda *a, **kw: clicks.append(a[-1]))
    monkeypatch.setattr(live.time, "sleep", lambda *a: None)
    assert live.build_fixed(object(), "OFR/42-", object(), 1, (1000, 1000)) is scene
    assert len(clicks) == 4
    assert "WH_RECOVERY=effect_verified_after_2_reads" in capsys.readouterr().out


def test_active_tab_crop_follows_border_gap_not_other_visible_tabs():
    from app.agent.learning.windowhub_offer_editor import selected_tab_crop_box

    rgb = frame("builder_01_empty.png")
    row = selected_row_box(rgb)
    rgb[100:174, :] = (238, 240, 252)
    rgb[125:150, 120:310] = (220, 180, 200)
    rgb[150:154, 40:1500] = (156, 193, 182)
    rgb[149, 40:1500] = (171, 173, 179)
    rgb[149, 210:310] = (156, 193, 182)
    assert selected_row_box(rgb) == row
    assert selected_tab_crop_box(rgb).x == 212
    rgb[149, 120:180] = (156, 193, 182)
    assert selected_tab_crop_box(rgb) is None


def test_selected_draft_retries_binding_with_visual_proof(monkeypatch):
    scope = object()
    check = lambda rgb: True
    binding = []
    monkeypatch.setattr(live, "inspect", lambda loop: object())
    monkeypatch.setattr(live, "observe_selected_draft_tab", lambda *args: ("dokument15", check))

    def bind(*args, visual_draft_check=None):
        binding.append(visual_draft_check)
        return scope if visual_draft_check is check else None

    monkeypatch.setattr(live.NewOfferHandoff, "bind_selected_draft", bind)
    monkeypatch.setattr(live, "verify_editor_transition", lambda *args, **kwargs: True)
    monkeypatch.setattr(live, "build_construction", lambda *args, **kwargs: None)
    assert live.build_selected_draft(object(), object(), "Dokument15", (1000, 1000), construction="ur") == 0
    assert binding == [None, check]


def test_active_mode_uses_the_verified_selected_draft_name(monkeypatch, capsys):
    scope = object()
    binding = []
    monkeypatch.setattr(live, "inspect", lambda loop: object())
    monkeypatch.setattr(live, "active_native_draft_name", lambda *args: None)
    check = lambda rgb: True
    monkeypatch.setattr(live, "observe_selected_draft_tab", lambda scene, api, name: (
        ("dokument21", check) if name is None else None
    ))

    def bind(scene, api, name, *, visual_draft_check=None):
        binding.append((name, visual_draft_check))
        return scope

    monkeypatch.setattr(live.NewOfferHandoff, "bind_selected_draft", bind)
    monkeypatch.setattr(live, "verify_editor_transition", lambda *args, **kwargs: True)
    monkeypatch.setattr(live, "build_construction", lambda *args, **kwargs: None)
    assert live.build_selected_draft(object(), object(), "active", (1000, 1000), construction="ur") == 0
    assert binding == [("dokument21", check)]
    assert "WH_DRAFT_TARGET=dokument21" in capsys.readouterr().out


def test_geometry_verifies_blue_frame_when_old_palette_ratios_cannot():
    from app.agent.learning.windowhub_builder_replay import observe_builder_stage, read_builder_stage

    drawing = np.full((280, 280, 3), 255, dtype=np.uint8)
    for strip in (drawing[:12], drawing[-12:], drawing[:, :12], drawing[:, -12:]):
        strip[:] = (0, 0, 255)
    assert read_builder_stage(drawing) == "unknown"
    assert observe_builder_stage(drawing) == "frame"
    drawing[-12:, 12:-12] = 255
    assert observe_builder_stage(drawing) == "unknown"


def test_next_position_rechecks_completed_window_and_waits_for_owned_wizard(monkeypatch, capsys):
    scope = NS(frame=200, child=203, pid=50)
    api = NS(pid=lambda hwnd: 50, parent=lambda hwnd, kind: 200, owner=lambda hwnd: 200 if hwnd == 204 else 0)
    completed, wizard = object(), object()
    invoked = []
    monkeypatch.setattr(live, "observe_workspace", lambda *args, **kwargs: (completed, None, None, None, "opening_marker"))
    monkeypatch.setattr(live, "find_draft_add_button", lambda *args: NS(
        iface_invoke=NS(Invoke=lambda: invoked.append(True)),
    ))
    monkeypatch.setattr(live, "owns_native_workspace", lambda *args: True)
    monkeypatch.setattr(live, "inspect", lambda loop: wizard)
    monkeypatch.setattr(live, "foreground_handle", lambda *args: 204)
    monkeypatch.setattr(live, "active_mdi_child", lambda *args: 203)
    monkeypatch.setattr(live, "stage_of", lambda *args: "position")
    live.open_draft_next_position(object(), scope, api, 1, (1000, 1000), opening=True)
    assert invoked == [True]
    assert "WH_NEXT_POSITION=wizard_open" in capsys.readouterr().out


def test_next_position_never_clicks_add_when_glazing_and_hardware_are_not_verified(monkeypatch):
    monkeypatch.setattr(live, "observe_workspace", lambda *args, **kwargs: (None, None, None, None, "sash"))
    monkeypatch.setattr(live, "find_draft_add_button", lambda *args: pytest.fail("must not find or click Add"))
    with pytest.raises(live.WorkspaceBlocked, match="next_position_previous_construction_unverified"):
        live.open_draft_next_position(object(), object(), object(), 1, (1000, 1000), opening=True)


def test_glazing_fallback_checks_expected_slot_and_ignores_neighboring_blue_button():
    from tools.check_windowhub_builder_sequence import TOOLBAR_CROP

    root = live.ROOT
    with Image.open(root / "dataset_archive/glass_tool/glass_tool.png") as image:
        template = np.asarray(image.convert("RGB").resize((33, 33), Image.Resampling.BILINEAR))
    left, top, right, bottom = TOOLBAR_CROP

    def toolbar(name):
        return frame(name)[top:bottom, left:right]

    frame_icon, sash_icon = (18, 421), (17, 462)
    hit = live.alternate_glazing_target(toolbar("builder_03_frame_sash.png.png"), template, frame_icon, sash_icon)
    assert hit is not None and 530 <= hit[1] <= 545
    # The neighboring blue button remains visible after glazing, when the
    # glazing slot itself is gray in this fixture.
    assert live.alternate_glazing_target(toolbar("builder_04_frame_sash_glass.png.png"), template, frame_icon, sash_icon) is None


def test_editor_draft_builds_second_supplied_position_after_owned_wizard(monkeypatch, capsys):
    scope = NS(bind_next_position=lambda scene, api: scene == "wizard")
    actions = []
    monkeypatch.setattr(live, "inspect", lambda loop: object())
    monkeypatch.setattr(live.NewOfferHandoff, "bind_selected_draft", lambda *args: scope)
    monkeypatch.setattr(live, "verify_editor_transition", lambda *args, **kw: True)
    monkeypatch.setattr(live, "build_construction", lambda loop, offer, api, number, size, **kw: actions.append(("build", number, size)))
    monkeypatch.setattr(live, "open_draft_next_position", lambda *args, **kw: "wizard")

    def run(loop, offer, api, *, width, height, **kw):
        assert offer is scope
        actions.append(("wizard", width, height))
        return 0

    monkeypatch.setattr(live, "run", run)
    assert live.build_selected_draft(
        object(), object(), "Dokument13", (1000, 1000), construction="ur", next_size=(1200, 1000),
    ) == 0
    assert actions == [("build", 1, (1000, 1000)), ("wizard", 1200, 1000), ("build", 2, (1200, 1000))]
    assert "WH_AUTONOMOUS_RESULT=verified_draft_positions:2" in capsys.readouterr().out
