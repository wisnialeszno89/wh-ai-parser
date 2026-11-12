"""Check the opening drawing against the five saved WindowHub builder screenshots."""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_opening_marker import read_opening_marker_side

FIXTURES = ROOT / "research/datasets/windowhub/builder_region/raw"
CANVAS_CROP = (45, 375, 350, 680)
EXPECTED = {
    "builder_01_empty.png": None,
    "builder_02_frame.png.png": None,
    "builder_03_frame_sash.png.png": None,
    "builder_04_frame_sash_glass.png.png": None,
    "builder_05_right_panel.png.png": "RIGHT",
}


def read_fixture(name):
    with Image.open(FIXTURES / name) as screenshot:
        return np.asarray(screenshot.convert("RGB").crop(CANVAS_CROP))


def main():
    matches = []
    for name, expected in EXPECTED.items():
        marker = read_opening_marker_side(read_fixture(name))
        matches.append(marker == expected)
        print(f"{name} MARKER_APEX={marker or 'UNKNOWN'}")
    print("WH_OPENING_MARKER_RESULT=" + ("verified" if all(matches) else "review"))
    return 0 if all(matches) else 2


if __name__ == "__main__":
    raise SystemExit(main())
