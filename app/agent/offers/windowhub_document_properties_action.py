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
