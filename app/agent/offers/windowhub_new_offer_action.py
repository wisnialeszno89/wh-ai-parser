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


def prepare_new_offer_from_workspace(scene: ScreenScene) -> PreparedWindowHubFormAction:
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
    if title != "Okna - Start1" and not title.casefold().startswith("okna - ofr/"):
        return blocked("WindowHub Start1 or offer document workspace must be active.")

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


def prepare_new_offer_from_start(scene: ScreenScene) -> PreparedWindowHubFormAction:
    """Legacy public entry: preserve strict Start1-only semantics."""
    if not isinstance(scene, ScreenScene):
        raise TypeError("new_offer_start_scene_required")
    title = getattr(scene.observation.state, "active_window_title", "") or ""
    if title != "Okna - Start1":
        from app.agent.offers.windowhub_offer_form_action import PreparedWindowHubFormAction, WindowHubFormActionStatus
        return PreparedWindowHubFormAction(
            field_name="start_new_offer",
            status=WindowHubFormActionStatus.BLOCKED,
            reason="WindowHub start workspace must be active.",
        )
    return prepare_new_offer_from_workspace(scene)


def prepare_start1_navigation_from_offer(scene: ScreenScene) -> PreparedWindowHubFormAction:
    """Navigate by the visible Start1 workspace tab, with exact UIA identity.

    This action does not close or save a document. Caller must verify that
    Start1 actually became the foreground stage before taking another action.
    """
    if not isinstance(scene, ScreenScene):
        raise TypeError("start1_navigation_scene_required")
    state = scene.observation.state
    app = (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    title = state.active_window_title or ""
    def blocked(reason):
        return PreparedWindowHubFormAction(
            field_name="navigate_start1",
            status=WindowHubFormActionStatus.BLOCKED,
            reason=reason,
        )
    if app != "okna.exe" or not title.casefold().startswith("okna - ofr/"):
        return blocked("Start1 navigation requires a currently active offer document.")
    controls = [
        e for e in scene.elements
        if e.kind == "button"
        and normalize_uia_text(e.label or "") == "start1"
        and (e.metadata or {}).get("source") in {
            "windows_ui_automation", "windowhub_ui_automation",
        }
        and (e.metadata or {}).get("uia_visible") is True
        and (e.metadata or {}).get("uia_enabled") is True
    ]
    if len(controls) != 1:
        return blocked(f"Expected one visible Start1 tab, found {len(controls)}.")
    element = controls[0]
    meta = element.metadata or {}
    runtime_id = meta.get("uia_runtime_id")
    if not isinstance(runtime_id, str) or not runtime_id.strip():
        return blocked("Start1 tab runtime identity missing.")
    if sum(
        1 for e in scene.elements
        if (e.metadata or {}).get("source") in {
            "windows_ui_automation", "windowhub_ui_automation"
        } and (e.metadata or {}).get("uia_runtime_id") == runtime_id
    ) != 1:
        return blocked("Start1 tab runtime identity is not unique.")
    target = SemanticTargetQuery(
        role="button",
        label=element.label,
        automation_id=meta.get("automation_id"),
        uia_runtime_id=runtime_id,
        description="Switch to WindowHub Start1 without closing existing offer",
    )
    return PreparedWindowHubFormAction(
        field_name="navigate_start1",
        status=WindowHubFormActionStatus.READY,
        reason="Unique Start1 workspace tab recognized.",
        action=AgentAction(
            name="click_screen_element",
            description="Switch to Start1 workspace; keep offer document open.",
            target=target,
            requires_environment_observation=True,
        ),
        expected_outcome=ExpectedOutcome(
            description="Start1 workspace is active after clicking tab.",
            expected_active_application="Okna.exe",
            expected_window_title="Okna - Start1",
        ),
        runtime_id=runtime_id,
    )
