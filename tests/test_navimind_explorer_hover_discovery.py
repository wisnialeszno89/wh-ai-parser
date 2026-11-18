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
