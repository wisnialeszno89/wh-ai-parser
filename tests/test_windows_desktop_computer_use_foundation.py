from types import SimpleNamespace

import pytest

from app.agent.environment.windows_desktop_environment_adapter import (
    ForegroundWindowSnapshot,
    WindowsDesktopEnvironmentAdapter,
)
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.windows_ui_automation_provider import (
    WindowsUIAutomationProvider,
)
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)
from app.runtime.execution.robot_action_executor import RobotExecutionMode
from app.runtime.execution.vision.bridges.execution_safety_gate import (
    ExecutionSafetyGate,
)
from app.runtime.execution.window.window_rect import WindowRect


def _snapshot():
    return ForegroundWindowSnapshot(
        handle=501,
        title="Workbook - Excel",
        rect=WindowRect(left=20, top=30, width=1200, height=800),
        active_application="EXCEL.EXE",
        root_owner_handle=501,
    )


def test_windows_desktop_adapter_observes_the_injected_foreground_window():
    screenshot = SimpleNamespace(width=1200, height=800)
    calls = []
    adapter = WindowsDesktopEnvironmentAdapter(
        snapshot_provider=_snapshot,
        screenshot_engine=SimpleNamespace(
            capture=lambda rect: calls.append(rect) or screenshot
        ),
    )

    observation = adapter.observe()

    assert calls == [_snapshot().rect]
    assert observation.state.active_application == "EXCEL.EXE"
    assert observation.state.active_window_title == "Workbook - Excel"
    assert observation.state.screen_width == 1200
    assert observation.state.screen_height == 800
    assert observation.metadata["source"] == "windows_desktop"
    assert observation.metadata["window_handle"] == 501
    assert observation.metadata["window_focused"] is True
    assert observation.metadata["foreground_window_handle"] == 501
    assert observation.metadata["window_root_owner_handle"] == 501
    assert observation.metadata["screenshot"] is screenshot


def test_windows_desktop_adapter_fails_closed_without_a_valid_snapshot():
    adapter = WindowsDesktopEnvironmentAdapter(
        snapshot_provider=lambda: None,
        screenshot_engine=SimpleNamespace(
            capture=lambda _rect: pytest.fail("capture must not run")
        ),
    )

    with pytest.raises(TypeError, match="snapshot_invalid"):
        adapter.observe()


def test_windows_ui_automation_provider_marks_elements_as_generic_windows_uia(
    monkeypatch,
):
    element = ScreenElement(
        kind="button",
        label="Save",
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windowhub_ui_automation",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_runtime_id": "[1,2,3]",
        },
    )
    monkeypatch.setattr(
        WindowHubUIAutomationProvider,
        "perceive",
        lambda _self, _observation: (element,),
    )

    provider = WindowsUIAutomationProvider()
    result = provider.perceive(SimpleNamespace())

    assert len(result) == 1
    assert result[0].metadata["source"] == "windows_ui_automation"
    assert result[0].metadata["provider_family"] == "windows_desktop"


def test_robot_gui_executor_accepts_generic_windows_uia_targets():
    element = ScreenElement(
        kind="button",
        label="Save",
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_runtime_id": "[1,2,3]",
        },
    )

    assert RobotGUIExecutor._is_uia_only_target(element) is True


def test_safety_gate_accepts_trusted_windows_uia_provenance():
    metadata = {
        "source": "windows_ui_automation",
        "uia_enabled": True,
        "uia_visible": True,
        "uia_control_type": "button",
    }

    assert ExecutionSafetyGate().can_execute_uia_element(
        metadata=metadata,
        interaction_capability=InteractionCapability.CLICKABLE,
        interaction_capability_confidence=0.99,
        require_foreground=False,
    ) is True


def _robot_gui_executor(loop):
    return next(
        executor
        for executor in loop.verification_loop.execution_engine.registry.all()
        if isinstance(executor, RobotGUIExecutor)
    )


def test_windows_desktop_control_loop_defaults_to_dry_run(monkeypatch):
    monkeypatch.delenv("COMPUTER_USE_LIVE", raising=False)

    loop = create_windows_desktop_agent_control_loop()

    assert _robot_gui_executor(loop).robot_action_executor.mode is (
        RobotExecutionMode.DRY_RUN
    )
    assert isinstance(
        loop.environment_runtime.adapter,
        WindowsDesktopEnvironmentAdapter,
    )
    assert isinstance(
        loop.perception_engine.providers[0],
        WindowsUIAutomationProvider,
    )


def test_windows_desktop_control_loop_requires_explicit_live_opt_in(
    monkeypatch,
):
    monkeypatch.setenv("COMPUTER_USE_LIVE", "1")

    loop = create_windows_desktop_agent_control_loop()

    assert _robot_gui_executor(loop).robot_action_executor.mode is (
        RobotExecutionMode.LIVE
    )
