import subprocess

import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.environment.windows_desktop_environment_adapter import DesktopWindowSnapshot
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_evidence import EvidenceKind, EvidenceSource, SemanticEvidence
from app.agent.runtime import navimind_windowhub_scene_reader as reader
from app.runtime.execution.window.window_rect import WindowRect


def properties_scene():
    rect = WindowRect(114, 241, 869, 752)
    title = "Właściwości dokumentu"
    windows = (DesktopWindowSnapshot(25, title, rect, "Okna.exe", 10, True),)
    metadata = {"window_rect": rect, "window_handle": 25, "desktop_windows": windows}
    evidence = SemanticEvidence(
        EvidenceSource.ACCESSIBILITY, EvidenceKind.BOUNDS, (10, 20, 30, 40),
        element_id="uia:25",
    )
    customer_picker = ScreenElement(
        kind="combobox", label="Zamawiający",
        metadata={
            "automation_id": "IDC_ZAMAWIAJACY",
            "uia_runtime_id": "25",
            "uia_ancestor_structure": ({"automation_id": "properties"},),
            "semantic_evidence": (evidence,),
        },
        interaction_capability=InteractionCapability.CLICKABLE, evidence=(evidence,),
    )
    return ScreenScene(
        EnvironmentObservation(EnvironmentState("Okna.exe", title), metadata),
        (customer_picker,), metadata,
    )


def test_windowhub_scene_round_trip_preserves_local_control_evidence():
    scene = properties_scene()
    assert reader.decode_scene(reader.encode_scene(scene).encode()) == scene


def test_uia_timeout_retries_a_read_only_child_and_returns_fresh_scene(monkeypatch):
    fresh = properties_scene()
    attempts = []

    def run(command, **kwargs):
        attempts.append(kwargs["timeout"])
        assert kwargs["env"]["COMPUTER_USE_LIVE"] == "0"
        assert kwargs["env"]["WH_REAL_WINDOWHUB"] == "0"
        assert "NAVIMIND_AGENT_V2_SECRET" not in kwargs["env"]
        assert "AI_GATEWAY_API_KEY" not in kwargs["env"]
        if len(attempts) == 1:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return subprocess.CompletedProcess(command, 0, reader.encode_scene(fresh).encode())

    monkeypatch.setenv("COMPUTER_USE_LIVE", "1")
    monkeypatch.setenv("WH_REAL_WINDOWHUB", "1")
    monkeypatch.setenv("NAVIMIND_AGENT_V2_SECRET", "test-only")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "test-only")
    monkeypatch.setattr(reader.subprocess, "run", run)
    assert reader.observe_windowhub() == fresh
    assert attempts == [4, 8]


def test_two_failed_reads_report_timeout_without_a_third_attempt(monkeypatch):
    attempts = []

    def run(command, **kwargs):
        attempts.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(reader.subprocess, "run", run)
    with pytest.raises(reader.WindowHubReadTimeout, match="windowhub_uia_reader_timed_out"):
        reader.observe_windowhub()
    assert attempts == [4, 8]
