from __future__ import annotations

import os

import pytest

if os.name != "nt":
    pytest.skip(
        "RobotActionExecutor integration tests require Windows ctypes.windll.",
        allow_module_level=True,
    )

from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_action_executor import (
    RobotActionExecutor,
    RobotExecutionMode,
)
from app.runtime.execution.windowhub_mdi_tab_activator import (
    WindowHubMdiTabActivationResult,
)


class AllowUIASafetyGate:
    def __init__(self):
        self.calls = []

    def can_execute_uia_element(self, **kwargs):
        self.calls.append(kwargs)
        return True


class ExplodingMouse:
    def click(self, *_args, **_kwargs):
        raise AssertionError(
            "Document-tab activation must not fall back to a coordinate click."
        )


def make_tab_element():
    return ScreenElement(
        kind="text",
        label="Start1",
        x=50,
        y=137,
        width=81,
        height=21,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windowhub_ui_automation",
            "semantic_name": "Start1",
            "provider_element_id": "uia:Start1",
            "uia_runtime_id": "runtime:Start1",
            "uia_control_type": "tabitem",
            "uia_tab_scope": "document",
            "uia_document_tab_selected": False,
            "uia_enabled": True,
            "uia_visible": True,
            "interaction_capability_confidence": 0.99,
        },
    )


def test_uia_document_tab_uses_verified_mdi_activator_not_mouse(monkeypatch):
    calls = []
    expected = WindowHubMdiTabActivationResult(
        success=True,
        executed=True,
        target_label="Start1",
        before_selected=False,
        after_selected=True,
        active_before_target=False,
        active_after_target=True,
        reason="Native MDI activation verified.",
    )

    def fake_activator(**kwargs):
        calls.append(kwargs)
        return expected

    monkeypatch.setattr(
        "app.runtime.execution.windowhub_mdi_tab_activator.activate_windowhub_mdi_document_tab",
        fake_activator,
    )
    gate = AllowUIASafetyGate()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=gate,
        mouse=ExplodingMouse(),
    )

    result = executor.execute_uia_screen_element(
        screen_element=make_tab_element(),
        action=InteractionAction.CLICK,
        screen_origin=(0, 0),
        window_handle=100,
        root_window_handle=100,
    )

    assert result.success is True
    assert result.executed is True
    assert result.reason == "Native MDI activation verified."
    assert len(calls) == 1
    assert calls[0]["target_label"] == "Start1"
    assert calls[0]["window_handle"] == 100
    assert calls[0]["live"] is True
    assert len(gate.calls) == 1


def test_failed_mdi_activation_fails_closed_without_mouse_fallback(monkeypatch):
    calls = []
    expected = WindowHubMdiTabActivationResult(
        success=False,
        executed=False,
        target_label="Start1",
        before_selected=False,
        reason="UIA selected state conflicts with the native active MDI document.",
    )

    def fake_activator(**kwargs):
        calls.append(kwargs)
        return expected

    monkeypatch.setattr(
        "app.runtime.execution.windowhub_mdi_tab_activator.activate_windowhub_mdi_document_tab",
        fake_activator,
    )
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=AllowUIASafetyGate(),
        mouse=ExplodingMouse(),
    )

    result = executor.execute_uia_screen_element(
        screen_element=make_tab_element(),
        action=InteractionAction.CLICK,
        screen_origin=(0, 0),
        window_handle=100,
        root_window_handle=100,
    )

    assert result.success is False
    assert result.executed is False
    assert "conflicts" in result.reason
    assert len(calls) == 1


def test_dry_run_document_tab_uses_non_live_mdi_validation(monkeypatch):
    calls = []
    expected = WindowHubMdiTabActivationResult(
        success=True,
        executed=False,
        target_label="Start1",
        before_selected=False,
        after_selected=False,
        active_before_target=False,
        active_after_target=False,
        reason="DRY_RUN verified the unique document tab; no activation attempted.",
    )

    def fake_activator(**kwargs):
        calls.append(kwargs)
        return expected

    monkeypatch.setattr(
        "app.runtime.execution.windowhub_mdi_tab_activator.activate_windowhub_mdi_document_tab",
        fake_activator,
    )
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.DRY_RUN,
        safety_gate=AllowUIASafetyGate(),
        mouse=ExplodingMouse(),
    )

    result = executor.execute_uia_screen_element(
        screen_element=make_tab_element(),
        action=InteractionAction.CLICK,
        screen_origin=(0, 0),
        window_handle=100,
        root_window_handle=100,
    )

    assert result.success is True
    assert result.executed is False
    assert calls[0]["live"] is False


def test_fused_visual_primary_can_use_explicit_uia_provenance_for_document_tab(monkeypatch):
    from dataclasses import replace

    calls = []

    def fake_activator(**kwargs):
        calls.append(kwargs)
        return WindowHubMdiTabActivationResult(
            success=True,
            executed=True,
            target_label="Start1",
            before_selected=False,
            after_selected=True,
            active_before_target=False,
            active_after_target=True,
            reason="Native MDI activation verified.",
        )

    monkeypatch.setattr(
        "app.runtime.execution.windowhub_mdi_tab_activator.activate_windowhub_mdi_document_tab",
        fake_activator,
    )
    element = make_tab_element()
    fused = replace(
        element,
        metadata={
            **dict(element.metadata or {}),
            "source": "windowhub_vision",
            "fusion_sources": (
                "windowhub_ui_automation",
                "windowhub_vision",
            ),
        },
    )
    gate = AllowUIASafetyGate()
    executor = RobotActionExecutor(
        mode=RobotExecutionMode.LIVE,
        safety_gate=gate,
        mouse=ExplodingMouse(),
    )

    result = executor.execute_uia_screen_element(
        screen_element=fused,
        action=InteractionAction.CLICK,
        screen_origin=(0, 0),
        window_handle=100,
        root_window_handle=100,
    )

    assert result.success is True
    assert len(calls) == 1
    assert gate.calls[0]["metadata"]["source"] == "windowhub_ui_automation"
