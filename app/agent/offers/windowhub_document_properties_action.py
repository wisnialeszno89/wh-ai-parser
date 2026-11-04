"""Guarded WindowHub document price exclusions based on UIA TogglePattern state."""
from __future__ import annotations

from app.agent.agent_action import AgentAction
from app.agent.offers.windowhub_offer_form_action import (
    PreparedWindowHubFormAction, WindowHubFormActionStatus,
)
from app.agent.offers.windowhub_offer_form_map import normalize_uia_text
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.verification.expected_outcome import ExpectedOutcome


DOCUMENT_PRICE_EXCLUSIONS = {
    "exclude_construction_price": "Bez ceny konstrukcji",
    "exclude_installation_price": "Bez ceny montażu",
    "exclude_removal_price": "Bez ceny demontażu",
    "exclude_finishing_price": "Bez ceny wykończenia",
}
_UIA_SOURCES = frozenset({"windows_ui_automation", "windowhub_ui_automation"})


def prepare_price_exclusion(
    scene: ScreenScene, field_name: str
) -> PreparedWindowHubFormAction:
    """Prepare exactly one unchecked checkbox for a verified click."""

    def blocked(reason):
        return PreparedWindowHubFormAction(
            field_name=field_name,
            status=WindowHubFormActionStatus.BLOCKED,
            reason=reason,
        )

    if not isinstance(scene, ScreenScene):
        raise TypeError("windowhub_price_scene_required")
    label = DOCUMENT_PRICE_EXCLUSIONS.get(field_name)
    if label is None:
        return blocked("The requested price exclusion is not supported.")

    state = scene.observation.state
    application = state.active_application or ""
    if application.replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe":
        return blocked("WindowHub is not the foreground application.")
    if normalize_uia_text(state.active_window_title or "") != normalize_uia_text("Właściwości dokumentu"):
        return blocked("Document properties are not the foreground dialog.")

    candidates = [
        element for element in scene.elements
        if (
            element.kind == "checkbox"
            and normalize_uia_text(element.label or "") == normalize_uia_text(label)
            and (element.metadata or {}).get("source") in _UIA_SOURCES
            and (element.metadata or {}).get("uia_enabled") is True
            and (element.metadata or {}).get("uia_visible") is True
        )
    ]
    if len(candidates) != 1:
        return blocked(f"Pricing checkbox is missing or ambiguous: {field_name}.")

    element = candidates[0]
    metadata = element.metadata or {}
    runtime_id = metadata.get("uia_runtime_id")
    if not isinstance(runtime_id, str) or not runtime_id.strip() or sum(
        1 for item in scene.elements
        if (item.metadata or {}).get("source") in _UIA_SOURCES
        and (item.metadata or {}).get("uia_runtime_id") == runtime_id
    ) != 1:
        return blocked("Pricing checkbox has no unique UIA RuntimeId.")

    checked = metadata.get("uia_checked")
    if checked is True:
        return PreparedWindowHubFormAction(
            field_name=field_name,
            status=WindowHubFormActionStatus.ALREADY_SATISFIED,
            reason=f"Pricing exclusion {field_name} is already enabled.",
            runtime_id=runtime_id,
        )
    if checked is not False:
        return blocked("Checkbox TogglePattern state unknown; do not toggle.")

    target = SemanticTargetQuery(
        role="checkbox",
        label=element.label,
        automation_id=metadata.get("automation_id"),
        uia_runtime_id=runtime_id,
        description=f"Enable the verified {field_name} pricing exclusion",
    )
    action = AgentAction(
        name="click_screen_element",
        description=f"Enable the currently unchecked {field_name} pricing exclusion.",
        target=target,
        requires_environment_observation=True,
    )
    expected = ExpectedOutcome(
        description=f"{field_name} checkbox is checked.",
        expected_element_label=element.label,
        expected_element_state_name="uia_checked",
        expected_element_state_value=True,
        expected_element_uia_runtime_id=runtime_id,
        expected_element_automation_id=metadata.get("automation_id"),
    )
    return PreparedWindowHubFormAction(
        field_name=field_name,
        status=WindowHubFormActionStatus.READY,
        reason="Checkbox has unique UIA evidence and is confirmed unchecked.",
        action=action,
        expected_outcome=expected,
        runtime_id=runtime_id,
    )


def prepare_document_confirmation(
    scene: ScreenScene, goal
) -> PreparedWindowHubFormAction:
    """Confirm only when the observed client and four exclusions are proven."""
    from app.agent.offers.windowhub_new_offer_mission import (
        NewWindowOfferGoal, NewWindowOfferMissionPlanner, OfferDecision,
    )

    def blocked(reason):
        return PreparedWindowHubFormAction(
            field_name="confirm_document",
            status=WindowHubFormActionStatus.BLOCKED,
            reason=reason,
        )

    if not isinstance(scene, ScreenScene):
        raise TypeError("windowhub_document_scene_required")
    if not isinstance(goal, NewWindowOfferGoal):
        raise TypeError("windowhub_document_goal_required")
    decision = NewWindowOfferMissionPlanner().decide(goal, scene)
    if decision.decision is not OfferDecision.CONFIRM_DOCUMENT:
        return blocked(f"Document is not ready for confirmation: {decision.decision.value}.")

    matches = [
        e for e in scene.elements
        if (
            e.kind == "button"
            and normalize_uia_text(e.label or "") == "ok"
            and (e.metadata or {}).get("source") in _UIA_SOURCES
            and (e.metadata or {}).get("uia_enabled") is True
            and (e.metadata or {}).get("uia_visible") is True
        )
    ]
    if len(matches) != 1:
        return blocked("Document OK button is missing or ambiguous.")
    element = matches[0]
    meta = element.metadata or {}
    runtime_id = meta.get("uia_runtime_id")
    if not isinstance(runtime_id, str) or not runtime_id.strip() or sum(
        1 for e in scene.elements
        if (e.metadata or {}).get("source") in _UIA_SOURCES
        and (e.metadata or {}).get("uia_runtime_id") == runtime_id
    ) != 1:
        return blocked("Document OK button has no unique RuntimeId.")

    target = SemanticTargetQuery(
        role="button", label=element.label,
        automation_id=meta.get("automation_id"),
        uia_runtime_id=runtime_id,
        description="Confirm WindowHub offer document properties",
    )
    return PreparedWindowHubFormAction(
        field_name="confirm_document",
        status=WindowHubFormActionStatus.READY,
        reason="Client and four exclusions verified; unique OK is ready.",
        action=AgentAction(
            name="click_screen_element",
            description="Confirm the validated new offer document properties.",
            target=target,
            requires_environment_observation=True,
        ),
        expected_outcome=ExpectedOutcome(
            description="WindowHub closes validated document properties.",
            expected_active_application="Okna.exe",
            require_scene_change=True,
        ),
        runtime_id=runtime_id,
    )


def prepare_defer_document_properties(
    scene: ScreenScene, goal
) -> PreparedWindowHubFormAction:
    """Use Cancel only for an explicitly deferred workflow; never assume its effect."""
    from app.agent.offers.windowhub_new_offer_mission import NewWindowOfferGoal

    def blocked(reason):
        return PreparedWindowHubFormAction(
            field_name="defer_document_properties",
            status=WindowHubFormActionStatus.BLOCKED,
            reason=reason,
        )

    if not isinstance(scene, ScreenScene) or not isinstance(goal, NewWindowOfferGoal):
        raise TypeError("windowhub_defer_goal_and_scene_required")
    if goal.customer_policy != "defer_to_salesperson":
        return blocked("Deferring client selection requires explicit user intent.")

    state = scene.observation.state
    application = state.active_application or ""
    if application.replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe":
        return blocked("WindowHub is not the active application.")
    if normalize_uia_text(state.active_window_title or "") != normalize_uia_text("Właściwości dokumentu"):
        return blocked("Document properties are not the active dialog.")

    candidates = [
        element for element in scene.elements
        if element.kind == "button"
        and normalize_uia_text(element.label or "") == "anuluj"
        and (element.metadata or {}).get("source") in _UIA_SOURCES
        and (element.metadata or {}).get("uia_control_type") == "button"
        and (element.metadata or {}).get("uia_enabled") is True
        and (element.metadata or {}).get("uia_visible") is True
    ]
    if len(candidates) != 1:
        return blocked(f"Expected one Cancel button in document properties; found {len(candidates)}.")
    element = candidates[0]
    meta = element.metadata or {}
    runtime_id = meta.get("uia_runtime_id")
    if not isinstance(runtime_id, str) or not runtime_id.strip():
        return blocked("Cancel button has no UIA runtime identity.")
    if sum(
        1 for item in scene.elements
        if (item.metadata or {}).get("source") in _UIA_SOURCES
        and (item.metadata or {}).get("uia_runtime_id") == runtime_id
    ) != 1:
        return blocked("Cancel button RuntimeId is not unique.")

    target = SemanticTargetQuery(
        role="button",
        label=element.label,
        automation_id=meta.get("automation_id"),
        uia_runtime_id=runtime_id,
        description="Defer document preferences to salesperson",
    )
    return PreparedWindowHubFormAction(
        field_name="defer_document_properties",
        status=WindowHubFormActionStatus.READY,
        reason="Explicit deferred mode; single observed Cancel button is ready.",
        action=AgentAction(
            name="click_screen_element",
            description="Skip document preferences for now; verify the resulting WindowHub stage.",
            target=target,
            requires_environment_observation=True,
        ),
        expected_outcome=ExpectedOutcome(
            description="After deferring document properties, the position wizard is active.",
            expected_active_application="Okna.exe",
            expected_window_title="Dodawanie nowej pozycji",
        ),
        runtime_id=runtime_id,
    )
