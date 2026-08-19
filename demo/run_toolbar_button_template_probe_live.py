from __future__ import annotations

import ctypes
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from app.runtime.execution.hardware_icon_template import load_hardware_icon_template
from app.wh.vision.opencv.opencv_adapter import OpenCVAdapter
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _toolbar_buttons, _get_window_rect

user32 = ctypes.windll.user32

TEMPLATE_MAP = {
    "FRAME": ["frame_tool.png", "frame_tool_1.png", "frame_tool_2.png", "frame_tool_3.png", "frame_tool_4.png", "frame_tool_5.png"],
    "SASH": ["frame_sash_tool.png", "sash_tool.png"],
    "GLASS": ["glass_tool.png"],
    "MULLION": ["insert_vertical_tool.png"],
    "HORIZONTAL_MULLION": ["insert_horizontal_tool.png"],
}

@dataclass
class Candidate:
    tool: str
    command_id: int
    index: int
    confidence: float
    template: str
    scale: float
    screen_rect: tuple[int, int, int, int]
    enabled: bool


def _find_root_hwnd() -> int:
    found: list[int] = []
    enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum
    def cb(hwnd: int, _lparam: int) -> bool:
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        if buf.value.strip() == "Okna -":
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(cb, 0)
    if not found:
        raise RuntimeError("WindowHub root window not found")
    return found[0]


def _capture_toolbar_image(vision, toolbar_rect):
    image = vision.screenshot.image
    left, top, width, height = toolbar_rect
    origin_left = int(vision.window.left)
    origin_top = int(vision.window.top)
    x0 = max(0, left - origin_left)
    y0 = max(0, top - origin_top)
    x1 = min(image.shape[1], x0 + width)
    y1 = min(image.shape[0], y0 + height)
    return image[y0:y1, x0:x1]


def _match_crop(cv: OpenCVAdapter, crop: np.ndarray, template: np.ndarray, scales=(0.55,0.65,0.75,0.85,0.95,1.0,1.05,1.15,1.25,1.35,1.4)):
    best = None
    for scale in scales:
        w = max(1, int(round(template.shape[1] * scale)))
        h = max(1, int(round(template.shape[0] * scale)))
        if w > crop.shape[1] or h > crop.shape[0]:
            continue
        resized = cv2.resize(template, (w, h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        result = cv.match_array(crop, resized)
        if best is None or result.confidence > best[0]:
            best = (result.confidence, scale, resized)
    return best


def _read_template(path: Path):
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        return None
    if len(image.shape) == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB TOOLBAR BUTTON TEMPLATE PROBE")
    print("=" * 80)
    print("SAFE MODE: no clicks.")

    vision = RuntimeVision().capture()
    root = _find_root_hwnd()
    toolbar = _find_toolbar(root, "Narzędzia")
    if toolbar is None:
        raise RuntimeError("Native Narzędzia toolbar was not found")
    toolbar_rect = _get_window_rect(toolbar)
    buttons = _toolbar_buttons(toolbar)
    toolbar_image = _capture_toolbar_image(vision, toolbar_rect)
    print(f"[PROBE] root={root} toolbar={toolbar} rect={toolbar_rect} buttons={len(buttons)}")

    templates_dir = Path("templates")
    cv = OpenCVAdapter()
    output_dir = Path("outputs/debug/toolbar_button_template_probe")
    output_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_dir / "toolbar.png"), toolbar_image)

    results: list[Candidate] = []
    for tool, filenames in TEMPLATE_MAP.items():
        best_candidate = None
        best_global = None
        for filename in filenames:
            template = _read_template(templates_dir / filename)
            if template is None:
                print(f"[MAP] {tool} missing template={filename}")
                continue
            for button in buttons:
                if not button.command_id or not button.screen_rect:
                    continue
                left, top, width, height = button.screen_rect
                tl, tt, _, _ = toolbar_rect
                rx = int(left - tl)
                ry = int(top - tt)
                crop = toolbar_image[max(0, ry):max(0, ry)+height, max(0, rx):max(0, rx)+width]
                if crop.size == 0:
                    continue
                match = _match_crop(cv, crop, template)
                if match is None:
                    continue
                conf, scale, _ = match
                candidate = Candidate(tool, button.command_id, button.index, float(conf), filename, float(scale), tuple(button.screen_rect), bool(button.state & 0x04))
                if best_global is None or conf > best_global.confidence:
                    best_global = candidate
                if button.state & 0x04:
                    if best_candidate is None or conf > best_candidate.confidence:
                        best_candidate = candidate
        chosen = best_candidate or best_global
        if chosen:
            results.append(chosen)
            print(f"[MAP] {tool:<20} conf={chosen.confidence:.3f} template={chosen.template} scale={chosen.scale:.2f} index={chosen.index} command_id={chosen.command_id} enabled={chosen.enabled} rect={chosen.screen_rect}")
        else:
            print(f"[MAP] {tool:<20} no template result")

    hardware_template = load_hardware_icon_template()
    best_hw = None
    for button in buttons:
        if not button.command_id or not button.screen_rect:
            continue
        left, top, width, height = button.screen_rect
        tl, tt, _, _ = toolbar_rect
        rx = int(left - tl); ry = int(top - tt)
        crop = toolbar_image[max(0, ry):max(0, ry)+height, max(0, rx):max(0, rx)+width]
        match = _match_crop(cv, crop, hardware_template)
        if match is not None:
            conf, scale, _ = match
            if best_hw is None or conf > best_hw.confidence:
                best_hw = Candidate("HARDWARE", button.command_id, button.index, float(conf), "embedded_hardware", float(scale), tuple(button.screen_rect), bool(button.state & 0x04))
    if best_hw:
        results.append(best_hw)
        print(f"[MAP] {'HARDWARE':<20} conf={best_hw.confidence:.3f} template=embedded_hardware scale={best_hw.scale:.2f} index={best_hw.index} command_id={best_hw.command_id} enabled={best_hw.enabled} rect={best_hw.screen_rect}")
    else:
        print("[MAP] HARDWARE             no template result")

    (output_dir / "mapping.json").write_text(json.dumps([asdict(x) for x in results], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[PROBE] Saved: {output_dir / 'mapping.json'}")
    print("[PROBE] COMPLETE. No clicks were sent.")


if __name__ == "__main__":
    main()
