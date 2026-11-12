import pytest

from app.agent.learning.windowhub_opening_marker import read_opening_marker_side
from tools.check_windowhub_opening_markers import EXPECTED, read_fixture


@pytest.mark.parametrize(("name", "expected"), EXPECTED.items())
def test_real_builder_sequence_reports_direction_only_when_marker_is_visible(name, expected):
    assert read_opening_marker_side(read_fixture(name)) == expected


def test_synthetic_mirror_of_hardware_screenshot_switches_marker_apex():
    image = read_fixture("builder_05_right_panel.png.png")

    assert read_opening_marker_side(image[:, ::-1]) == "LEFT"
