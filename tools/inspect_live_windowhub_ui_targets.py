from __future__ import annotations

import os
import sys
from pathlib import Path
import ctypes


ROOT = Path(__file__).resolve().parents[1]


def _foreground_process_info():
    if os.name != "nt":
        return None, None

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, None

    process_id = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(
        ctypes.c_void_p(hwnd),
        ctypes.byref(process_id),
    )

    pid = int(process_id.value)
    if pid <= 0:
        return None, None

    process_name = None
    handle = kernel32.OpenProcess(
        0x1000,  # PROCESS_QUERY_LIMITED_INFORMATION
        False,
        pid,
    )
    if handle:
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = ctypes.c_ulong(len(buffer))
            if kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(size),
            ):
                process_name = Path(buffer.value).name
        finally:
            kernel32.CloseHandle(handle)

    return pid, process_name
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)
from app.agent.perception.perception_engine import PerceptionEngine
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)


def _screen_point(element, window_rect):
    if not element.has_bounds:
        return None

    origin_x = int(getattr(window_rect, "left", 0))
    origin_y = int(getattr(window_rect, "top", 0))
    return (
        origin_x + int(element.x) + int(element.width) // 2,
        origin_y + int(element.y) + int(element.height) // 2,
    )


def main() -> int:
    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print("Set WH_REAL_WINDOWHUB=1 before running this diagnostic.")
        return 2

    environment = WindowHubEnvironmentAdapter()
    perception = PerceptionEngine(
        providers=(
            WindowHubVisionProvider(),
            WindowHubUIAutomationProvider(),
        ),
    )

    print("WindowHub semantic target inspection")
    print("===================================")
    print("No GUI action is executed by this tool.")
    print()

    observation = environment.observe()
    title = observation.state.active_window_title
    window_rect = observation.metadata.get("window_rect")
    foreground_pid, foreground_process = _foreground_process_info()

    print(f"active_window_title={title!r}")
    print(f"foreground_pid={foreground_pid!r}")
    print(f"foreground_process={foreground_process!r}")

    normalized_title = title.casefold() if title is not None else ""
    normalized_process = (
        foreground_process.casefold()
        if foreground_process is not None
        else ""
    )
    recognized_windowhub_title = (
        "windowhub" in normalized_title
        or normalized_title.startswith("okna -")
        or Path(normalized_process).stem == "okna"
    )

    if not recognized_windowhub_title:
        print(
            "WindowHub is not the active window; refusing inspection. "
            "Expected a WindowHub title, the production app title prefix "
            "'Okna -', or the foreground process 'Okna'."
        )
        return 3

    if window_rect is None:
        print("Window rect is unavailable; refusing inspection.")
        return 4

    print(
        "window_rect="
        f"left={getattr(window_rect, 'left', None)} "
        f"top={getattr(window_rect, 'top', None)} "
        f"width={getattr(window_rect, 'width', None)} "
        f"height={getattr(window_rect, 'height', None)}"
    )
    print()

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
            "screen_point": _screen_point(
                element,
                window_rect,
            ),
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
