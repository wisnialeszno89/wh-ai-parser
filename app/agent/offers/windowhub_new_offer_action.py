"""Verified Start1 -> New Offer action prepared from live UIA evidence."""
from __future__ import annotations

from app.agent.agent_action import AgentAction
from app.agent.offers.windowhub_offer_form_action import (
    PreparedWindowHubFormAction, WindowHubFormActionStatus,
)
from app.agent.offers.windowhub_offer_form_map import normalize_uia_text
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.verification.expected_outcome import ExpectedOutcome


def prepare_new_offer_from_start(scene: ScreenScene) -> PreparedWindowHubFormAction:
    def blocked(reason):
        return PreparedWindowHubFormAction(
            field_name="start_new_offer",
            status=WindowHubFormActionStatus.BLOCKED,
            reason=reason,
        )

    if not isinstance(scene, ScreenScene):
        raise TypeError("new_offer_start_scene_required")
    state = scene.observation.state
    app = getattr(state, "active_application", "") or ""
    title = getattr(state, "active_window_title", "") or ""
    if app.replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe":
        return blocked("WindowHub is not the active process.")
    if title != "Okna - Start1":
        return blocked("WindowHub start workspace must be active.")

    candidates = [
        element for element in scene.elements
        if (
            element.kind == "button"
            and normalize_uia_text(element.label or "") == "nowa oferta"
            and (element.metadata or {}).get("source") in {
                "windows_ui_automation", "windowhub_ui_automation"
            }
            and (element.metadata or {}).get("uia_enabled") is True
            and (element.metadata or {}).get("uia_visible") is True
        )
    ]
    if len(candidates) != 1:
        return blocked(f"Expected one clickable New Offer UIA button; found {len(candidates)}.")
    element = candidates[0]
    meta = element.metadata or {}
    runtime_id = meta.get("uia_runtime_id")
    if not isinstance(runtime_id, str) or not runtime_id.strip():
        return blocked("New Offer button has no UIA runtime identity.")
    if sum(
        1 for item in scene.elements
        if (item.metadata or {}).get("source") in {
            "windows_ui_automation", "windowhub_ui_automation"
        } and (item.metadata or {}).get("uia_runtime_id") == runtime_id
    ) != 1:
        return blocked("New Offer button runtime identity is not unique.")

    target = SemanticTargetQuery(
        role="button",
        label=element.label,
        automation_id=meta.get("automation_id"),
        uia_runtime_id=runtime_id,
        description="Open one new WindowHub offer",
    )
    return PreparedWindowHubFormAction(
        field_name="start_new_offer",
        status=WindowHubFormActionStatus.READY,
        reason="Uniquely verified New Offer UIA button is ready.",
        action=AgentAction(
            name="click_screen_element",
            description="Open a new unsaved WindowHub offer.",
            target=target,
            requires_environment_observation=True,
        ),
        expected_outcome=ExpectedOutcome(
            description="WindowHub document properties dialog appears.",
            expected_active_application="Okna.exe",
            expected_window_title="Właściwości dokumentu",
        ),
        runtime_id=runtime_id,
    )
