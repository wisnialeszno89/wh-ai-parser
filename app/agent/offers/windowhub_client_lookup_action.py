"""Open WindowHub customer lookup using the observed native LookupEdit button.

The picker is a separate capability: opening it never chooses a record.
"""
from __future__ import annotations

from app.agent.agent_action import AgentAction
from app.agent.offers.windowhub_offer_form_action import (
    PreparedWindowHubFormAction, WindowHubFormActionStatus,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.verification.expected_outcome import ExpectedOutcome


def prepare_open_customer_lookup(scene: ScreenScene) -> PreparedWindowHubFormAction:
    def blocked(reason):
        return PreparedWindowHubFormAction(
            field_name="open_customer_lookup",
            status=WindowHubFormActionStatus.BLOCKED,
            reason=reason,
        )

    if not isinstance(scene, ScreenScene):
        raise TypeError("windowhub_customer_lookup_scene_required")
    state = scene.observation.state
    application = state.active_application or ""
    if application.replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe":
        return blocked("WindowHub is not active.")
    if (state.active_window_title or "").strip().casefold() != "właściwości dokumentu":
        return blocked("Document properties dialog is not active.")

    candidates = [
        e for e in scene.elements
        if e.kind == "button"
        and e.label == "LookUpEdit"
        and (e.metadata or {}).get("automation_id") == "IDC_ZAMAWIAJACY"
        and (e.metadata or {}).get("source") in {
            "windowhub_ui_automation", "windows_ui_automation"
        }
        and (e.metadata or {}).get("uia_control_type") == "button"
        and (e.metadata or {}).get("uia_enabled") is True
        and (e.metadata or {}).get("uia_visible") is True
    ]
    if len(candidates) != 1:
        return blocked(f"Expected one customer lookup button; found {len(candidates)}.")
    element = candidates[0]
    meta = element.metadata or {}
    runtime_id = meta.get("uia_runtime_id")
    if not isinstance(runtime_id, str) or not runtime_id.strip():
        return blocked("Customer lookup has no UIA runtime identity.")
    if sum(
        1 for e in scene.elements
        if (e.metadata or {}).get("source") in {
            "windowhub_ui_automation", "windows_ui_automation"
        } and (e.metadata or {}).get("uia_runtime_id") == runtime_id
    ) != 1:
        return blocked("Customer lookup runtime identity is ambiguous.")

    target = SemanticTargetQuery(
        role="button", label="LookUpEdit",
        automation_id="IDC_ZAMAWIAJACY",
        uia_runtime_id=runtime_id,
        description="Open customer selection grid in document properties",
    )
    return PreparedWindowHubFormAction(
        field_name="open_customer_lookup",
        status=WindowHubFormActionStatus.READY,
        reason="Unique customer LookupEdit button is ready to open its grid.",
        action=AgentAction(
            name="click_screen_element",
            description="Open the customer lookup grid without choosing a customer.",
            target=target,
            requires_environment_observation=True,
        ),
        expected_outcome=ExpectedOutcome(
            description="Customer lookup becomes visible for semantic inspection.",
            expected_active_application="Okna.exe",
            require_scene_change=True,
        ),
        runtime_id=runtime_id,
    )
