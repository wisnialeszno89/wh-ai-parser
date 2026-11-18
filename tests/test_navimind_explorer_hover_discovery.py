"""Pure unit tests for app-neutral Explorer discovery. No Windows input."""
from types import SimpleNamespace

from PIL import Image, ImageDraw

from tools.run_navimind_explorer_hover_v1 import (
    candidate_diagnostics, eligible_controls, visual_hover_candidates,
)


def _scene(elements=(), image=None):
    metadata = {}
    if image is not None:
        metadata["screenshot"] = SimpleNamespace(image=image)
    return SimpleNamespace(
        elements=tuple(elements),
        observation=SimpleNamespace(metadata=metadata),
    )


def test_no_uia_controls_does_not_prevent_visual_hover_candidates():
    img = Image.new("RGB", (360, 240), "white")
    d = ImageDraw.Draw(img)
    for x in (30, 90, 150, 210, 270):
        d.rectangle((x, 40, x + 26, 66), outline="black", width=3)
        d.line((x + 3, 44, x + 22, 62), fill="black", width=3)
    scene = _scene(image=img)
    assert eligible_controls(scene, limit=12) == []
    assert candidate_diagnostics(scene)["uia_elements"] == 0
    found = visual_hover_candidates(scene, limit=4)
    assert 1 <= len(found) <= 4
    assert all(e.metadata["source"] == "visual_exploration" for e in found)


def test_no_image_is_no_visual_candidate():
    assert visual_hover_candidates(_scene(), limit=5) == []


def test_uia_filter_reports_reason_without_granting_click():
    element = SimpleNamespace(
        kind="button", label="Tool", x=10, y=15, width=24, height=24,
        has_bounds=True,
        metadata={
            "source": "windows_ui_automation", "uia_visible": True,
            "uia_enabled": True, "uia_runtime_id": "[native1]",
        },
    )
    scene = _scene(elements=(element,))
    assert candidate_diagnostics(scene)["unique_runtime_ids"] == 1
    assert eligible_controls(scene, limit=5) == [element]


def test_mss_bgra_numpy_screenshot_finds_visual_regions():
    import numpy as np
    img = Image.new("RGB", (360, 240), "white")
    d = ImageDraw.Draw(img)
    for x in (30, 90, 150, 210, 270):
        d.rectangle((x, 40, x + 26, 66), outline="black", width=3)
        d.line((x + 3, 44, x + 22, 62), fill="black", width=3)
    rgb = np.asarray(img)
    bgra = np.concatenate(
        [rgb[:, :, ::-1], np.full((*rgb.shape[:2], 1), 255, dtype=np.uint8)],
        axis=2,
    )
    scene = _scene(image=bgra)
    found = visual_hover_candidates(scene, limit=4)
    assert 1 <= len(found) <= 4
    assert all(e.metadata["source"] == "visual_exploration" for e in found)



def test_visual_hover_difference_detects_popup_away_from_pointer():
    from tools.run_navimind_explorer_hover_v1 import visual_hover_difference
    initial = Image.new("RGB", (220, 160), "white")
    hovered = initial.copy()
    draw = ImageDraw.Draw(hovered)
    draw.rectangle((90, 50, 195, 86), fill="black")
    result = visual_hover_difference(initial, hovered, pointer=(35, 34))
    assert result["visual_change"] is True
    assert result["changed_pixels"] > 100
    assert result["changed_bounds"] == [90, 50, 196, 87]


def test_visual_hover_difference_ignores_pointer_only_change():
    from tools.run_navimind_explorer_hover_v1 import visual_hover_difference
    initial = Image.new("RGB", (220, 160), "white")
    hovered = initial.copy()
    draw = ImageDraw.Draw(hovered)
    draw.rectangle((35, 35, 41, 41), fill="black")
    result = visual_hover_difference(initial, hovered, pointer=(38, 37))
    assert result["visual_change"] is False
    assert result["changed_pixels"] == 0
