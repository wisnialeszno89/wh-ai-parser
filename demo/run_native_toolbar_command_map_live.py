from __future__ import annotations

import ctypes
from pathlib import Path

import cv2

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from app.wh.vision.opencv.opencv_adapter import OpenCVAdapter
from app.runtime.execution.vision.vision_adapter import VisionAdapter
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _get_window_rect, _toolbar_buttons

user32 = ctypes.windll.user32

SCALES = (0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.0)
TOOLS = (
    GuiTool.FRAME,
    GuiTool.SASH,
    GuiTool.GLASS,
    GuiTool.MULLION,
    GuiTool.HORIZONTAL_MULLION,
    GuiTool.HARDWARE,
)


def _match_tool(toolbar_image, template_path: Path, cv: OpenCVAdapter):
    template = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
    if template is None:
        raise RuntimeError(f"Cannot read template: {template_path}")

    best = None
    for scale in SCALES:
        width = max(1, int(round(template.shape[1] * scale)))
        height = max(1, int(round(template.shape[0] * scale)))
        if width > toolbar_image.shape[1] or height > toolbar_image.shape[0]:
            continue
        resized = cv2.resize(
            template,
            (width, height),
            interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
        )
        result = cv.match_array(toolbar_image, resized)
        center = (
            result.x + result.width / 2.0,
            result.y + result.height / 2.0,
        )
        candidate = (result.confidence, scale, result.x, result.y, result.width, result.height, center)
        if best is None or result.confidence > best[0]:
            best = candidate
    return best


def _button_for_center(buttons, center, toolbar_rect):
    cx, cy = center
    for button in buttons:
        rect = button.screen_rect
        if not rect:
            continue
        sx, sy, sw, sh = rect
        # Convert screen rect to toolbar-local coordinates.
        lx = sx - toolbar_rect[0]
        ly = sy - toolbar_rect[1]
        if lx <= cx <= lx + sw and ly <= cy <= ly + sh:
            return button
    return None


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR COMMAND MAP PROBE")
    print("=" * 80)
    print("DO NOT CLICK.")

    vision = RuntimeVision().capture()
    root_hwnd = int(user32.GetForegroundWindow())
    if not root_hwnd:
        raise RuntimeError("Unable to determine foreground WindowHub HWND")

    # Prefer exact title match through EnumWindows helper used by previous probes.
    title = "Okna -"
    enum_matches = []
    enum_proc_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum_proc_type
    def enum_cb(hwnd, _lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(max(length + 1, 256))
        user32.GetWindowTextW(hwnd, buf, len(buf))
        if buf.value.strip() == title:
            enum_matches.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(enum_cb, 0)
    root_hwnd = enum_matches[0] if enum_matches else root_hwnd
    print(f"[WINDOW] root_hwnd={root_hwnd}")

    toolbar = _find_toolbar(root_hwnd, "Narzędzia")
    if toolbar is None:
        raise RuntimeError("Native Narzędzia toolbar not found")

    toolbar_rect = _get_window_rect(toolbar)
    print(f"[NATIVE TOOLBAR] hwnd={toolbar} rect={toolbar_rect}")

    buttons = _toolbar_buttons(toolbar)
    print(f"[NATIVE TOOLBAR] buttons={len(buttons)}")

    left, top, width, height = toolbar_rect
    # The vision screenshot is rooted at the full WindowHub window origin.
    origin_x = vision.window.left
    origin_y = vision.window.top
    local_x = left - origin_x
    local_y = top - origin_y
    toolbar_image = vision.screenshot.image[local_y:local_y + height, local_x:local_x + width]
    print(f"[NATIVE TOOLBAR] image crop={toolbar_image.shape[1]}x{toolbar_image.shape[0]}")

    adapter = VisionAdapter()
    cv = OpenCVAdapter()

    for tool in TOOLS:
        template_names = adapter.mapping.get(tool, [])
        best_global = None
        best_name = None
        for name in template_names:
            path = Path("templates") / name
            if not path.exists():
                continue
            match = _match_tool(toolbar_image, path, cv)
            if match and (best_global is None or match[0] > best_global[0]):
                best_global = match
                best_name = name

        if best_global is None:
            print(f"[MAP] {tool.name:<20} no template result")
            continue

        confidence, scale, x, y, w, h, center = best_global
        native_button = _button_for_center(buttons, center, toolbar_rect)
        if native_button is None:
            print(
                f"[MAP] {tool.name:<20} conf={confidence:.3f} "
                f"template={best_name} center={center} native_button=None"
            )
            continue

        print(
            f"[MAP] {tool.name:<20} conf={confidence:.3f} scale={scale:.2f} "
            f"template={best_name} center=({center[0]:.1f},{center[1]:.1f}) "
            f"-> index={native_button.index} command_id={native_button.command_id} "
            f"screen_rect={native_button.screen_rect} enabled={bool(native_button.state & 0x04)}"
        )

    print("[MAP] DO NOT CLICK. Command mapping probe complete.")


if __name__ == "__main__":
    main()
