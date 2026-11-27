"""Local read-only WindowHub scene capture in a disposable process."""
from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.environment.windows_desktop_environment_adapter import DesktopWindowSnapshot
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_evidence import (
    EvidenceKind, EvidenceSource, SemanticEvidence,
)
from app.runtime.execution.window.window_rect import WindowRect

ROOT = Path(__file__).resolve().parents[3]
MAX_SCENE_BYTES = 12 * 1024 * 1024


class WindowHubReadTimeout(TimeoutError):
    pass


def encode_scene(scene: ScreenScene) -> str:
    return json.dumps(asdict(scene), ensure_ascii=True, allow_nan=False)


def decode_scene(data: bytes) -> ScreenScene:
    if not data or len(data) > MAX_SCENE_BYTES:
        raise ValueError("windowhub_scene_size_invalid")
    payload = json.loads(data)
    observation = payload["observation"]
    metadata = observation["metadata"]
    metadata["window_rect"] = WindowRect(**metadata["window_rect"])
    metadata["desktop_windows"] = tuple(
        DesktopWindowSnapshot(**{**window, "rect": WindowRect(**window["rect"])})
        for window in metadata["desktop_windows"]
    )
    elements = []
    for row in payload["elements"]:
        row["interaction_capability"] = InteractionCapability(row["interaction_capability"])
        row["evidence"] = tuple(_decode_evidence(item) for item in row["evidence"])
        element_metadata = row["metadata"]
        if element_metadata is not None:
            for key in ("uia_ancestor_structure", "uia_ancestor_runtime_structure", "fusion_sources"):
                if key in element_metadata:
                    element_metadata[key] = tuple(element_metadata[key])
            if "uia_ancestor_context" in element_metadata:
                element_metadata["uia_ancestor_context"] = tuple(
                    tuple(entry) for entry in element_metadata["uia_ancestor_context"]
                )
            if "semantic_evidence" in element_metadata:
                element_metadata["semantic_evidence"] = tuple(
                    _decode_evidence(item) for item in element_metadata["semantic_evidence"]
                )
        elements.append(ScreenElement(**row))
    return ScreenScene(
        EnvironmentObservation(EnvironmentState(**observation["state"]), metadata),
        tuple(elements),
        {**payload["metadata"], **metadata},
    )


def _decode_evidence(item: dict) -> SemanticEvidence:
    item["source"] = EvidenceSource(item["source"])
    item["kind"] = EvidenceKind(item["kind"])
    if item["kind"] == EvidenceKind.BOUNDS and isinstance(item["value"], list):
        item["value"] = tuple(item["value"])
    return SemanticEvidence(**item)


def _read_once(*, timeout: float) -> ScreenScene:
    env = {
        key: value for key, value in os.environ.items()
        if not key.upper().startswith("NAVIMIND_")
        and key.upper() not in {"AI_GATEWAY_API_KEY", "OPENAI_API_KEY"}
    }
    env.update(COMPUTER_USE_LIVE="0", WH_REAL_WINDOWHUB="0")
    result = subprocess.run(
        [sys.executable, "-m", __name__], cwd=ROOT, env=env,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=timeout, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise RuntimeError("windowhub_uia_reader_failed")
    return decode_scene(result.stdout)


def observe_windowhub() -> ScreenScene:
    """Retry a stalled observation in a fresh process after killing the first."""
    for attempt, timeout in enumerate((4.0, 8.0), start=1):
        try:
            return _read_once(timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"NAVIMIND_WINDOWHUB_UIA_TIMEOUT_ATTEMPT={attempt}", flush=True)
    raise WindowHubReadTimeout("windowhub_uia_reader_timed_out")


def main() -> int:
    if os.name != "nt":
        return 2

    import pythoncom
    from app.agent.environment.windows_desktop_environment_adapter import (
        WindowsDesktopEnvironmentAdapter,
    )
    from app.agent.perception.perception_engine import PerceptionEngine
    from app.agent.perception.windows_desktop_window_provider import WindowsDesktopWindowProvider
    from app.agent.perception.windows_ui_automation_provider import WindowsUIAutomationProvider

    pythoncom.CoInitialize()
    try:
        with redirect_stdout(sys.stderr):
            adapter = WindowsDesktopEnvironmentAdapter(capture_pixels=False)
            observation = adapter.observe()
            app = (observation.state.active_application or "").replace(chr(92), "/").rsplit("/", 1)[-1]
            providers = (WindowsDesktopWindowProvider(),)
            if app.casefold() == "okna.exe":
                providers += (WindowsUIAutomationProvider(),)
            scene = PerceptionEngine(providers=providers).perceive(observation)
            foreground = adapter._capture_foreground_window()
            if (
                foreground.handle != observation.metadata["window_handle"]
                or (foreground.title or "").strip() != (observation.state.active_window_title or "")
            ):
                return 4
            encoded = encode_scene(scene)
    finally:
        pythoncom.CoUninitialize()
    if len(encoded) > MAX_SCENE_BYTES:
        return 3
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
