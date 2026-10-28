from __future__ import annotations

from types import SimpleNamespace

import os

import pytest

if os.name != "nt":
    pytest.skip(
        "RobotActionExecutor integration tests require Windows ctypes.windll.",
        allow_module_level=True,
    )

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.execution.robot_gui_executor import RobotGUIExecutor
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.execution_context import ExecutionContext
from app.runtime.execution.interactions.interaction_action import InteractionAction
from app.runtime.execution.robot_action_executor import (
    RobotActionResult,
    RobotExecutionMode,
)


class RecordingRobotExecutor:
    def __init__(self):
        self.calls = []

    def execute_uia_screen_element(self, **kwargs):
        self.calls.append(kwargs)
        return RobotActionResult(
            success=True,
            action=InteractionAction.CLICK,
            mode=RobotExecutionMode.DRY_RUN,
            executed=False,
            target_id="uia:test-tab",
            reason="DRY_RUN: MDI activation path selected; no state change.",
        )


def make_context(*, foreground=100, foreground_owner=100):
    observation = SimpleNamespace(
        state=SimpleNamespace(
            active_application="WindowHub",
            active_window_title="Okna - OFR/Test <>",
        ),
        metadata={
            "source": "windowhub",
            "window_handle": 100,
            "foreground_window_handle": foreground,
            "foreground_root_owner_handle": foreground_owner,
            "window_rect": SimpleNamespace(left=0, top=0),
        },
    )
    element = ScreenElement(
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
            "uia_control_type": "tabitem",
            "uia_tab_scope": "document",
            "uia_document_tab_selected": False,
            "uia_enabled": True,
            "uia_visible": True,
            "uia_runtime_id": "uia:runtime-only",
            "interaction_capability_confidence": 0.99,
        },
    )
    scene = ScreenScene(
        observation=observation,
        elements=(element,),
        metadata={"active_document": "OFR/Test"},
    )
    request = AgentRequest(
        message="Activate the Start1 document tab.",
        session_id="windowhub-mdi-tab-test",
        salesman_id="test",
        metadata={},
    )
    return ExecutionContext(request=request, current_scene=scene), element


def test_robot_gui_executor_routes_document_tabs_to_verified_mdi_path():
    context, element = make_context()
    robot = RecordingRobotExecutor()
    executor = RobotGUIExecutor(robot_action_executor=robot)

    result = executor.execute(
        AgentAction(
            name="click_screen_element",
            target="Start1",
            description="Activate the Start1 document tab.",
        ),
        context,
    )

    assert result.success is True
    assert result.requires_manual_review is False
    assert result.metadata["execution_path"] == "windowhub_mdi_tab"
    assert result.metadata["executed"] is False
    assert len(robot.calls) == 1
    assert robot.calls[0]["screen_element"] is element
    assert robot.calls[0]["action"] is InteractionAction.CLICK
    assert robot.calls[0]["window_handle"] == 100
    assert robot.calls[0]["root_window_handle"] == 100


def test_windowhub_execution_boundary_never_substitutes_unrelated_foreground_app():
    context, _ = make_context(foreground=500, foreground_owner=400)

    assert RobotGUIExecutor._window_handle(context) == 100


def test_owned_windowhub_dialog_remains_the_action_boundary():
    context, _ = make_context(foreground=300, foreground_owner=100)

    assert RobotGUIExecutor._window_handle(context) == 300
    assert RobotGUIExecutor._root_window_handle(context) == 100


def test_document_tab_routing_requires_explicit_uia_mdi_evidence():
    _, element = make_context()
    assert RobotGUIExecutor._is_windowhub_document_tab_target(element)

    unsafe = ScreenElement(
        kind="tabitem",
        label="Start1",
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windowhub_ui_automation",
            "uia_control_type": "tabitem",
            "uia_document_tab_selected": False,
            # Missing proven MDI document scope.
        },
    )
    assert not RobotGUIExecutor._is_windowhub_document_tab_target(unsafe)
