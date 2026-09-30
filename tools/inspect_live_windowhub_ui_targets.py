from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _windowhub_hwnd():
    if os.name != "nt":
        return None

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    candidates = []

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    def callback(candidate_hwnd, _):
        process_id = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(
            ctypes.c_void_p(candidate_hwnd),
            ctypes.byref(process_id),
        )
        pid = int(process_id.value)
        if pid <= 0:
            return True

        handle = kernel32.OpenProcess(
            0x1000,  # PROCESS_QUERY_LIMITED_INFORMATION
            False,
            pid,
        )
        if not handle:
            return True

        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = ctypes.c_ulong(len(buffer))
            ok = kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(size),
            )
            if not ok or Path(buffer.value).stem.casefold() != "okna":
                return True
        finally:
            kernel32.CloseHandle(handle)

        if not user32.IsWindowVisible(
            ctypes.c_void_p(candidate_hwnd)
        ):
            return True

        rect = RECT()
        if not user32.GetWindowRect(
            ctypes.c_void_p(candidate_hwnd),
            ctypes.byref(rect),
        ):
            return True

        width = int(rect.right - rect.left)
        height = int(rect.bottom - rect.top)
        if width <= 0 or height <= 0:
            return True

        title_buffer = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(
            ctypes.c_void_p(candidate_hwnd),
            title_buffer,
            len(title_buffer),
        )

        area = width * height
        candidates.append((
            area,
            int(candidate_hwnd),
            title_buffer.value,
            int(rect.left),
            int(rect.top),
            width,
            height,
        ))
        return True

    enum_windows_proc = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )
    user32.EnumWindows(enum_windows_proc(callback), 0)

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _window_title(hwnd):
    if not hwnd:
        return None
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    buffer = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(
        ctypes.c_void_p(hwnd),
        buffer,
        len(buffer),
    )
    return buffer.value


def _window_rect(hwnd):
    if not hwnd:
        return None
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    rect = RECT()
    if not user32.GetWindowRect(
        ctypes.c_void_p(hwnd),
        ctypes.byref(rect),
    ):
        return None

    return (
        int(rect.left),
        int(rect.top),
        int(rect.right - rect.left),
        int(rect.bottom - rect.top),
    )


def main() -> int:
    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print("Set WH_REAL_WINDOWHUB=1 before running this diagnostic.")
        return 2

    print("WindowHub semantic target inspection")
    print("===================================")
    print("No GUI action is executed by this tool.")
    print()

    hwnd = _windowhub_hwnd()
    title = _window_title(hwnd)
    rect = _window_rect(hwnd)

    print(f"windowhub_hwnd={hwnd!r}")
    print(f"windowhub_title={title!r}")
    print(f"windowhub_rect={rect!r}")

    if hwnd is None:
        print("Okna.exe main window was not found; refusing inspection.")
        return 3

    if rect is None:
        print("Window rect is unavailable; refusing inspection.")
        return 4

    from types import SimpleNamespace

    from app.agent.environment.environment_observation import (
        EnvironmentObservation,
    )
    from app.agent.environment.environment_state import (
        EnvironmentState,
    )
    from app.agent.perception.perception_engine import PerceptionEngine
    from app.agent.perception.windowhub_ui_automation_provider import (
        WindowHubUIAutomationProvider,
    )
    from app.agent.perception.windowhub_vision_provider import (
        WindowHubVisionProvider,
    )
    from app.runtime.execution.window.window_rect import WindowRect

    left, top, width, height = rect

    window_rect = WindowRect(
        left=left,
        top=top,
        width=width,
        height=height,
    )

    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application=None,
            active_window_title=title,
            screen_width=width,
            screen_height=height,
        ),
        metadata={
            "source": "windowhub",
            "window_rect": window_rect,
        },
    )

    perception = PerceptionEngine(
        providers=(
            WindowHubVisionProvider(),
            WindowHubUIAutomationProvider(
                desktop_factory=(
                    lambda: __import__("pywinauto").Desktop(backend="uia")
                ),
            ),
        ),
    )

    scene = perception.perceive(observation)

    print(f"provider_count={scene.metadata.get('provider_count')}")
    print(f"raw_element_count={scene.metadata.get('raw_element_count')}")
    print(f"fused_element_count={scene.metadata.get('element_count')}")
    print(f"merged_group_count={scene.metadata.get('merged_group_count')}")
    print()

    targets = []

    for element in scene.elements:
        metadata = dict(element.metadata or {})
        if (
            metadata.get("source") != "windowhub_ui_automation"
            and "uia_control_type" not in metadata
        ):
            continue

        targets.append({
            "label": element.label,
            "kind": element.kind,
            "automation_id": metadata.get("automation_id"),
            "uia_control_type": metadata.get("uia_control_type"),
            "enabled": metadata.get("uia_enabled"),
            "visible": metadata.get("uia_visible"),
            "interaction_capability": (
                element.interaction_capability.value
            ),
            "interaction_capability_confidence": metadata.get(
                "interaction_capability_confidence"
            ),
            "tracked_object_id": metadata.get("tracked_object_id"),
            "correlation": metadata.get("correlation"),
            "local_bounds": (
                element.x,
                element.y,
                element.width,
                element.height,
            ),
            "screen_point": (
                left + int(element.x) + int(element.width) // 2,
                top + int(element.y) + int(element.height) // 2,
            ) if element.has_bounds else None,
            "fused": metadata.get("fused"),
            "fusion_sources": metadata.get("fusion_sources"),
        })

    targets.sort(
        key=lambda item: (
            (item["label"] or "").casefold(),
            (item["automation_id"] or "").casefold(),
        )
    )

    if not targets:
        print("No named interactive UIA targets were found.")
        return 0

    for index, target in enumerate(targets, start=1):
        print(f"[{index}] {target['label']!r}")
        print(f"    kind={target['kind']}")
        print(
            "    automation_id="
            f"{target['automation_id']!r}"
        )
        print(
            "    uia_control_type="
            f"{target['uia_control_type']!r}"
        )
        print(f"    enabled={target['enabled']}")
        print(f"    visible={target['visible']}")
        print(
            "    interaction_capability="
            f"{target['interaction_capability']}"
        )
        print(
            "    interaction_capability_confidence="
            f"{target['interaction_capability_confidence']}"
        )
        print(
            "    tracked_object_id="
            f"{target['tracked_object_id']!r}"
        )
        print(
            "    correlation="
            f"{target['correlation']!r}"
        )
        print(
            "    local_bounds="
            f"{target['local_bounds']}"
        )
        print(
            "    screen_point="
            f"{target['screen_point']}"
        )
        print(f"    fused={target['fused']}")
        print(
            "    fusion_sources="
            f"{target['fusion_sources']}"
        )
        print()

    print("=== EXECUTABLE CANDIDATES ===")
    executable = [
        target
        for target in targets
        if (
            target["enabled"] is True
            and target["visible"] is True
            and target["tracked_object_id"]
            and target["interaction_capability"] == "clickable"
            and target["screen_point"] is not None
        )
    ]

    if not executable:
        print(
            "No UIA target currently satisfies all "
            "execution prerequisites."
        )
        return 0

    for target in executable:
        print(
            f"{target['label']!r} | "
            f"AutomationId={target['automation_id']!r} | "
            f"tracked={target['tracked_object_id']} | "
            f"screen_point={target['screen_point']}"
        )

    print()
    print("Inspection complete. No click was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
