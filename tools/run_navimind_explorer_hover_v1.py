"""NaviMind Explorer V1: bounded, app-neutral UIA hover discovery.

No clicks, typing, model calls, or background work. Only temporary cursor
motion over unique UIA button controls in the explicitly selected foreground
application. Stop if foreground window/process changes. This is an
experimental read-only reconnaissance utility, not autonomous task execution.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)

INTERACTIVE_ROLES = frozenset({"button", "radiobutton", "checkbox"})
UIA_SOURCES = frozenset({"windows_ui_automation", "windowhub_ui_automation"})
DENY_WORDS = (
    "zapisz", "save", "usuń", "usun", "delete", "zamknij", "close", "anuluj",
    "cancel", "zatwierd", "wyślij", "wyslij", "send", "drukuj", "print",
    "order", "zamów", "zamow", "checkout", "payment", "płatno", "platno",
)


def eligible_controls(scene, *, limit: int) -> list:
    """Candidate discovery is never proof that a control is safe to click."""
    seen = set()
    selected = []
    for e in scene.elements:
        m = e.metadata or {}
        if e.kind not in INTERACTIVE_ROLES or m.get("source") not in UIA_SOURCES:
            continue
        if m.get("uia_visible") is not True or m.get("uia_enabled") is not True:
            continue
        if not e.has_bounds or not 8 <= e.width <= 160 or not 8 <= e.height <= 100:
            continue
        label = (e.label or "").strip()
        if any(word in label.casefold() for word in DENY_WORDS):
            continue
        identity = m.get("uia_runtime_id")
        if not isinstance(identity, str) or not identity.strip() or identity in seen:
            continue
        seen.add(identity)
        selected.append(e)
        if len(selected) >= limit:
            break
    return selected


def candidate_diagnostics(scene) -> dict[str, int]:
    """Show why the original strict UIA candidate selector found nothing."""
    counts = {
        "scene_elements": len(scene.elements),
        "uia_elements": 0, "interactive_roles": 0,
        "visible_enabled": 0, "sized": 0,
        "unique_runtime_ids": 0,
    }
    seen = set()
    for e in scene.elements:
        m = e.metadata or {}
        if m.get("source") not in UIA_SOURCES:
            continue
        counts["uia_elements"] += 1
        if e.kind not in INTERACTIVE_ROLES:
            continue
        counts["interactive_roles"] += 1
        if m.get("uia_visible") is not True or m.get("uia_enabled") is not True:
            continue
        counts["visible_enabled"] += 1
        if not e.has_bounds or not 8 <= e.width <= 160 or not 8 <= e.height <= 100:
            continue
        counts["sized"] += 1
        ident = m.get("uia_runtime_id")
        if isinstance(ident, str) and ident.strip() and ident not in seen:
            seen.add(ident)
            counts["unique_runtime_ids"] += 1
    return counts


def visual_hover_candidates(scene, *, limit: int) -> list:
    """Image-based discovery only; candidates NEVER authorize clicks.

    Locate high-contrast patches in likely toolbar bands. The visual rank is
    merely a hover hypothesis, not an icon classification or UI capability.
    """
    screenshot = scene.observation.metadata.get("screenshot")
    image = getattr(screenshot, "image", None)
    if image is None:
        return []
    try:
        from PIL import Image, ImageFilter, ImageStat
        # MSSScreenshotEngine provides a NumPy BGRA array rather than a
        # PIL.Image. Accept both representations without silently failing.
        if isinstance(image, Image.Image):
            gray = image.convert("L")
        else:
            import numpy as np
            pixels = np.asarray(image)
            if pixels.ndim == 3 and pixels.shape[2] in (3, 4):
                # MSS channel order is BGR(A); edges need luminance only.
                rgb = np.ascontiguousarray(pixels[:, :, :3][:, :, ::-1])
                gray = Image.fromarray(rgb).convert("L")
            elif pixels.ndim == 2:
                gray = Image.fromarray(pixels.astype("uint8")).convert("L")
            else:
                return []
        w, h = gray.size
        if w < 160 or h < 120:
            return []
        edge = gray.filter(ImageFilter.FIND_EDGES)
        # Search toolbar-like areas: upper 30% and outer 18% of the sides.
        tile = 36
        stride = 36
        scored = []
        for y in range(36, h - tile, stride):
            for x in range(8, w - tile, stride):
                if not (y < int(h * .30) or x < int(w * .18)
                        or x > int(w * .82)):
                    continue
                crop = edge.crop((x, y, x + tile, y + tile))
                stat = ImageStat.Stat(crop)
                score = stat.mean[0] + .25 * stat.stddev[0]
                if score < 14:
                    continue
                scored.append((score, x, y))
        scored.sort(reverse=True)
        selected = []
        for score, x, y in scored:
            # Spread hovers across distinct regions; no dense sampling of text.
            if any(abs(x - prev.x) < tile * 2 and abs(y - prev.y) < tile * 2
                   for prev in selected):
                continue
            selected.append(SimpleNamespace(
                kind="visual_hover_region",
                label="visual_region_" + str(len(selected) + 1),
                x=x, y=y, width=tile, height=tile,
                metadata={"source": "visual_exploration",
                          "visual_edge_score": round(float(score), 2)},
            ))
            if len(selected) >= limit:
                break
        return selected
    except (ImportError, AttributeError, ValueError, TypeError) as exc:
        print("EXPLORER_VISUAL_ERROR=" + type(exc).__name__, flush=True)
        return []


def screenshot_rgb(scene):
    """Convert native MSS BGRA or PIL capture to a PIL RGB image."""
    from PIL import Image
    import numpy as np
    screenshot = scene.observation.metadata.get("screenshot")
    raw = getattr(screenshot, "image", None)
    if raw is None:
        return None
    if isinstance(raw, Image.Image):
        return raw.convert("RGB")
    pixels = np.asarray(raw)
    if pixels.ndim == 3 and pixels.shape[2] in (3, 4):
        return Image.fromarray(
            np.ascontiguousarray(pixels[:, :, :3][:, :, ::-1]),
            "RGB",
        )
    if pixels.ndim == 2:
        return Image.fromarray(pixels.astype("uint8"), "L").convert("RGB")
    return None


def visual_hover_difference(before_image, after_image, *, pointer: tuple[int, int]):
    """Find image differences outside cursor pixels. Evidence, not tooltip proof."""
    import numpy as np
    if before_image is None or after_image is None:
        return {"changed_pixels": 0, "changed_bounds": None, "visual_change": False}
    before = np.asarray(before_image.convert("RGB"), dtype=np.int16)
    after = np.asarray(after_image.convert("RGB"), dtype=np.int16)
    if before.shape != after.shape or before.ndim != 3:
        return {"changed_pixels": 0, "changed_bounds": None, "visual_change": False}
    mask = np.max(np.abs(before - after), axis=2) >= 28
    x, y = pointer
    # Ignore the cursor itself; not tooltip blocks extending away from it.
    mask[max(0, y - 16):y + 24, max(0, x - 16):x + 24] = False
    ys, xs = np.where(mask)
    pixels = int(xs.size)
    bbox = None
    if pixels:
        bbox = [int(xs.min()), int(ys.min()),
                int(xs.max()) + 1, int(ys.max()) + 1]
    return {
        "changed_pixels": pixels,
        "changed_bounds": bbox,
        "visual_change": pixels >= 80,
    }


def control_text(scene) -> set[str]:
    """Collect only short, visible UIA labels. Avoid customer text field contents."""
    result = set()
    for e in scene.elements:
        m = e.metadata or {}
        if m.get("source") not in UIA_SOURCES or m.get("uia_visible") is not True:
            continue
        if e.kind not in {"text", "tooltip", "button", "radiobutton", "checkbox"}:
            continue
        value = (e.label or "").strip()
        if 2 <= len(value) <= 100:
            result.add(value)
    return result


def current_foreground():
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise RuntimeError("no_foreground_window")
    from psutil import Process
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    process = Process(pid.value).name().casefold()
    return int(hwnd), process


def window_origin(scene) -> tuple[int, int]:
    rect = scene.observation.metadata.get("window_rect")
    if rect is None:
        raise RuntimeError("window_rect_missing")
    return int(rect.left), int(rect.top)


def explore(*, expected_process: str, limit: int, hover_seconds: float, output: Path, start_delay: int = 6) -> int:
    if os.name != "nt":
        print("EXPLORER_STOP=windows_required")
        return 2
    if not expected_process or "/" in expected_process or "\\" in expected_process:
        print("EXPLORER_STOP=invalid_process")
        return 2
    if not 1 <= limit <= 30 or not .3 <= hover_seconds <= 3:
        print("EXPLORER_STOP=invalid_limits")
        return 2
    if not 0 <= start_delay <= 20:
        print("EXPLORER_STOP=invalid_start_delay")
        return 2
    print("EXPLORER_PREPARE=Switch focus to the target application now", flush=True)
    time.sleep(start_delay)
    hwnd, process = current_foreground()
    if process != expected_process.casefold():
        print("EXPLORER_STOP=foreground_process_mismatch ACTUAL=" + process)
        return 4
    if process == "okna.exe":
        # Business orders are never a learning playground.
        from app.agent.runtime.windowhub_foreground_inspection import inspect_current_windowhub_foreground
        if not inspect_current_windowhub_foreground():
            print("EXPLORER_STOP=unverified_windowhub_foreground")
            return 4
    loop = create_windows_desktop_agent_control_loop()
    scene = loop.observe_scene()
    if (scene.observation.state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold() != process:
        print("EXPLORER_STOP=observed_process_mismatch")
        return 4
    title = (scene.observation.state.active_window_title or "").casefold()
    if process == "okna.exe" and ("zlc/" in title or "zamówienie" in title or "zamowienie" in title):
        print("EXPLORER_STOP=business_order_not_allowed")
        return 4
    x0, y0 = window_origin(scene)
    win_rect = scene.observation.metadata.get("window_rect")
    if win_rect is None:
        raise RuntimeError("window_rect_missing")
    visible_width = int(win_rect.width)
    visible_height = int(win_rect.height)
    if visible_width <= 0 or visible_height <= 0:
        raise RuntimeError("window_dimensions_invalid")
    diagnostic = candidate_diagnostics(scene)
    print("EXPLORER_UIA_DIAGNOSTICS=" + json.dumps(diagnostic), flush=True)
    candidates = eligible_controls(scene, limit=limit)
    discovery_mode = "uia"
    if not candidates:
        # WindowHub and custom-drawn software often paint toolbar icons
        # without exporting conventional accessible Button controls.
        candidates = visual_hover_candidates(scene, limit=limit)
        discovery_mode = "visual_hover_hypotheses"
    before = control_text(scene)
    baseline_image = screenshot_rgb(scene)
    frames_dir = output.parent / (output.stem + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    if baseline_image is not None:
        baseline_image.save(frames_dir / "baseline.png")
    user32 = ctypes.windll.user32
    cursor_start = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(cursor_start))
    output.parent.mkdir(parents=True, exist_ok=True)
    results = []
    print("EXPLORER_MODE=HOVER_ONLY_NO_CLICKS", flush=True)
    print("EXPLORER_DISCOVERY_MODE=" + discovery_mode, flush=True)
    print("EXPLORER_CANDIDATES=" + str(len(candidates)), flush=True)
    print("EXPLORER_PROCESS=" + process, flush=True)
    try:
        for idx, e in enumerate(candidates):
            current_hwnd, current_process = current_foreground()
            if current_hwnd != hwnd or current_process != process:
                print("EXPLORER_STOP=foreground_changed")
                break
            mx = e.x + e.width // 2
            my = e.y + e.height // 2
            if not (2 <= mx < visible_width - 2 and 2 <= my < visible_height - 2):
                continue
            user32.SetCursorPos(x0 + mx, y0 + my)
            time.sleep(hover_seconds)
            current_hwnd, current_process = current_foreground()
            if current_hwnd != hwnd or current_process != process:
                print("EXPLORER_STOP=foreground_changed_during_hover")
                break
            after_scene = loop.observe_scene()
            observed = sorted(control_text(after_scene) - before)
            hover_image = screenshot_rgb(after_scene)
            difference = visual_hover_difference(
                baseline_image, hover_image, pointer=(mx, my)
            )
            if hover_image is not None:
                hover_image.save(frames_dir / ("hover_" + str(idx).zfill(2) + ".png"))
            record = {
                "index": idx,
                "kind": e.kind,
                "label": e.label,
                "automation_id": (e.metadata or {}).get("automation_id"),
                "rect_relative": [e.x, e.y, e.width, e.height],
                "new_visible_labels": observed[:12],
                "image_difference": difference,
                "hover_at_relative": [mx, my],
                "outcome": "hover_observed_no_click",
            }
            results.append(record)
            print("HOVER_" + str(idx) + "=" + (e.label or "(unnamed)")[:65]
                  + " NEW_LABELS=" + str(len(observed))
                  + " CHANGED_PIXELS=" + str(difference["changed_pixels"])
                  + " VISUAL_CHANGE=" + str(difference["visual_change"]), flush=True)
            # Do not reuse a stale baseline: tooltips can persist between hovers.
            before = control_text(after_scene)
    finally:
        user32.SetCursorPos(cursor_start.x, cursor_start.y)
    output.write_text(json.dumps({
        "schema": "navimind.explorer.hover.v1",
        "application": process,
        "window_title": scene.observation.state.active_window_title,
        "mode": "hover_only",
        "discovery_mode": discovery_mode,
        "uia_diagnostics": diagnostic,
        "records": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("EXPLORER_ACTIONS_CLICKED=0")
    print("EXPLORER_OUTPUT=" + str(output))
    print("EXPLORER_FRAMES_FOLDER=" + str(frames_dir))
    print("EXPLORER_HOVERS=" + str(len(results)))
    print("EXPLORER_NOTE=Review labels for customer details before sharing.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Application-neutral hover-only UI explorer")
    parser.add_argument("--process", required=True, help="Expected foreground process, e.g. Okna.exe")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--hover-seconds", type=float, default=0.9)
    parser.add_argument("--start-delay", type=int, default=6)
    parser.add_argument("--output", type=Path, default=Path("explorer_hover_results.json"))
    args = parser.parse_args()
    return explore(expected_process=args.process, limit=args.limit,
                   hover_seconds=args.hover_seconds, output=args.output,
                   start_delay=args.start_delay)


if __name__ == "__main__":
    raise SystemExit(main())
