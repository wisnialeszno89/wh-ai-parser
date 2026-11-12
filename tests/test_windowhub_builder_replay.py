import numpy as np
import pytest
from PIL import Image

from app.agent.learning.windowhub_builder_replay import match_archived_toolbar
from tools.check_windowhub_builder_sequence import FIXTURES, TOOLBAR_CROP, observe_archive_frame


@pytest.mark.parametrize(("name", "stage", "tool", "target", "effect"), [
    ("builder_01_empty.png", "empty", "FRAME", (20, 581), "frame"),
    ("builder_02_frame.png.png", "frame", "SASH", (20, 621), "sash"),
    ("builder_03_frame_sash.png.png", "sash", "GLASS", (20, 697), "glass"),
    ("builder_04_frame_sash_glass.png.png", "glass", "HARDWARE", (20, 780), "opening_marker"),
    ("builder_05_right_panel.png.png", "opening_marker", None, None, None),
])
def test_archived_frame_selects_the_next_tool_in_the_expected_toolbar_slot(name, stage, tool, target, effect):
    with Image.open(FIXTURES / name) as image:
        actual_stage, actual_tool, actual_effect, match = observe_archive_frame(image)

    assert actual_stage == stage
    assert (actual_tool.name if actual_tool else None) == tool
    assert actual_effect == effect
    if target is None:
        assert match is None
    else:
        assert match is not None
        assert abs(match.x + TOOLBAR_CROP[0] - target[0]) <= 4
        assert abs(match.y + TOOLBAR_CROP[1] - target[1]) <= 4


def test_repeated_toolbar_icon_requires_review():
    template = np.array([[0, 20, 55], [40, 255, 90], [180, 70, 15]], dtype=np.uint8)
    toolbar = np.zeros((30, 8), dtype=np.uint8)
    toolbar[4:7, 2:5] = template
    toolbar[20:23, 2:5] = template

    assert match_archived_toolbar(toolbar, template) is None
