"""Replay saved WH screenshots: observe a stage, locate its next tool, check the next frame."""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_builder_replay import NEXT_STEP, match_archived_toolbar, read_builder_stage
from app.gui.enums.gui_tool import GuiTool
from tools.check_windowhub_opening_markers import CANVAS_CROP, FIXTURES

TOOLBAR_CROP = (0, 160, 42, 1100)
ARCHIVED_TEMPLATES = {
    GuiTool.FRAME: ("frame/frame_tool_1.png", 1.0),
    GuiTool.SASH: ("sash_tool.png", 0.30),
    GuiTool.GLASS: ("glass_tool.png", 0.30),
    GuiTool.HARDWARE: ("hardware_tool.png", 0.18),
}
EXPECTED_STAGES = ("empty", "frame", "sash", "glass", "opening_marker")


def observe_archive_frame(image):
    stage = read_builder_stage(np.asarray(image.convert("RGB").crop(CANVAS_CROP)))
    if stage not in NEXT_STEP:
        return stage, None, None, None
    tool, effect = NEXT_STEP[stage]
    template_path, scale = ARCHIVED_TEMPLATES[tool]
    with Image.open(ROOT / "templates" / template_path) as source:
        template = source.convert("L").resize(
            (round(source.width * scale), round(source.height * scale)),
            Image.Resampling.BILINEAR,
        )
    toolbar = image.convert("L").crop(TOOLBAR_CROP)
    match = match_archived_toolbar(np.asarray(toolbar), np.asarray(template))
    return stage, tool, effect, match


def main():
    frames = sorted(FIXTURES.glob("builder_*.png"))
    observed = []
    for frame in frames:
        with Image.open(frame) as image:
            observed.append(observe_archive_frame(image))
    verified = tuple(stage for stage, _, _, _ in observed) == EXPECTED_STAGES
    for index, (stage, tool, effect, match) in enumerate(observed):
        if tool is None:
            print(f"{frames[index].name} STAGE={stage} NEXT=none")
            continue
        next_stage = observed[index + 1][0] if index + 1 < len(observed) else None
        passed = match is not None and next_stage == effect
        verified &= passed
        target = f"{match.x + TOOLBAR_CROP[0]},{match.y + TOOLBAR_CROP[1]}" if match else "UNKNOWN"
        print(f"{frames[index].name} STAGE={stage} NEXT={tool.name} TARGET={target} "
              f"EXPECT={effect} OBSERVED={next_stage} MATCH={passed}")
    print("WH_BUILDER_REPLAY_RESULT=" + ("verified" if verified else "review"))
    return 0 if verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
