"""New-customer actions grounded in fresh WindowHub UIA evidence.

No coordinate paths or speculative IDs. The Add button and Firma input must
be uniquely observed. Creating a record is a persistent business operation.
"""
from __future__ import annotations

from app.agent.agent_action import AgentAction
from app.agent.offers.windowhub_offer_form_action import (
    PreparedWindowHubFormAction, WindowHubFormActionStatus,
)
from app.agent.offers.windowhub_offer_form_map import normalize_uia_text
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.verification.expected_outcome import ExpectedOutcome


_SOURCES = frozenset(("windowhub_ui_automation", "windows_ui_automation"))
_ADD_IDS = frozenset(("IDC_NEW",))


def _blocked(field, reason):
    return PreparedWindowHubFormAction(
        field_name=field, status=WindowHubFormActionStatus.BLOCKED, reason=reason,
    )


def _unique_control(scene, *, kind, label=None, automation_ids=()):
    candidates = []
    for element in scene.elements:
        meta = element.metadata or {}
        if (
            element.kind != kind
            or meta.get("source") not in _SOURCES
            or meta.get("uia_control_type") != kind
            or meta.get("uia_enabled") is not True
            or meta.get("uia_visible") is not True
        ):
            continue
        if automation_ids and meta.get("automation_id") not in automation_ids:
            continue
        if label is not None and not automation_ids and normalize_uia_text(element.label or "") != normalize_uia_text(label):
            continue
        candidates.append(element)
    if len(candidates) != 1:
        return None
    element = candidates[0]
    meta = element.metadata or {}
    rid = meta.get("uia_runtime_id")
    if not isinstance(rid, str) or not rid.strip():
        return None
    if sum(
        1 for item in scene.elements
        if (item.metadata or {}).get("source") in _SOURCES
        and (item.metadata or {}).get("uia_runtime_id") == rid
    ) != 1:
        return None
    return element


def _ready_click(field, element, *, description, expected):
    meta = element.metadata or {}
    return PreparedWindowHubFormAction(
        field_name=field,
        status=WindowHubFormActionStatus.READY,
        reason="Single verified UIA control.",
        action=AgentAction(
            name="click_screen_element", description=description,
            target=SemanticTargetQuery(
                role="button", label=element.label,
                automation_id=meta.get("automation_id"),
                uia_runtime_id=meta["uia_runtime_id"],
                description=description,
            ),
            requires_environment_observation=True,
        ),
        expected_outcome=expected,
        runtime_id=meta["uia_runtime_id"],
    )


def prepare_add_customer(scene: ScreenScene):
    if not isinstance(scene, ScreenScene):
        raise TypeError("new_customer_scene_required")
    state = scene.observation.state
    if (
        (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe"
        or normalize_uia_text(state.active_window_title or "") != "wlasciwosci dokumentu"
    ):
        return _blocked("new_customer_add", "Document properties not active.")
    button = _unique_control(
        scene, kind="button", label="OknaWPF", automation_ids=_ADD_IDS,
    )
    if button is None or (button.metadata or {}).get("automation_id") != "IDC_NEW":
        return _blocked(
            "new_customer_add",
            "Expected exactly one enabled customer Add button (IDC_NEW).",
        )
    return _ready_click(
        "new_customer_add", button,
        description="Open Add New Customer form from document properties.",
        expected=ExpectedOutcome(
            description="Native new customer dialog is visible.",
            expected_active_application="Okna.exe",
            expected_window_title="Zakładanie nowego klienta",
        ),
    )


def prepare_customer_name(scene: ScreenScene, customer_name: str):
    if not isinstance(scene, ScreenScene):
        raise TypeError("new_customer_scene_required")
    if not isinstance(customer_name, str) or not customer_name.strip() or len(customer_name.strip()) > 100:
        return _blocked("new_customer_name", "Invalid business name.")
    state = scene.observation.state
    if (
        (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe"
        or normalize_uia_text(state.active_window_title or "") != "zakladanie nowego klienta"
    ):
        return _blocked("new_customer_name", "New customer dialog not active.")
    field = _unique_control(scene, kind="edit", label="Firma")
    if field is None:
        return _blocked("new_customer_name", "Firma edit is not uniquely identified.")
    meta = field.metadata or {}
    if meta.get("current_value") == customer_name.strip():
        return PreparedWindowHubFormAction(
            field_name="new_customer_name", status=WindowHubFormActionStatus.ALREADY_SATISFIED,
            reason="Customer business name already equals request.",
            runtime_id=meta["uia_runtime_id"],
        )
    return PreparedWindowHubFormAction(
        field_name="new_customer_name", status=WindowHubFormActionStatus.READY,
        reason="One verified Firma edit can receive the requested business name.",
        action=AgentAction(
            name="write_text", description="Set the new customer business name.",
            target=SemanticTargetQuery(
                role="edit", label=field.label, automation_id=meta.get("automation_id"),
                uia_runtime_id=meta["uia_runtime_id"], description="Customer Firma",
            ),
            value=customer_name.strip(), requires_environment_observation=True,
        ),
        expected_outcome=ExpectedOutcome(
            description="New customer Firma matches requested name.",
            expected_active_application="Okna.exe",
            expected_window_title="Zakładanie nowego klienta",
            expected_element_label=field.label,
            expected_element_current_value=customer_name.strip(),
            expected_element_automation_id=meta.get("automation_id"),
            expected_element_uia_runtime_id=meta["uia_runtime_id"],
        ),
        runtime_id=meta["uia_runtime_id"],
    )


def prepare_confirm_new_customer(scene: ScreenScene, customer_name: str):
    if not isinstance(scene, ScreenScene):
        raise TypeError("new_customer_scene_required")
    state = scene.observation.state
    if (
        (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe"
        or normalize_uia_text(state.active_window_title or "") != "zakladanie nowego klienta"
    ):
        return _blocked("confirm_new_customer", "New customer dialog not active.")
    field = _unique_control(scene, kind="edit", label="Firma")
    if field is None or (field.metadata or {}).get("current_value") != customer_name:
        return _blocked("confirm_new_customer", "Customer name not independently verified.")
    ok = _unique_control(scene, kind="button", label="OK")
    if ok is None:
        return _blocked("confirm_new_customer", "Cannot uniquely identify customer OK button.")
    prepared = _ready_click(
        "confirm_new_customer", ok,
        description="Confirm newly named WindowHub customer record.",
        expected=ExpectedOutcome(
            description="New customer dialog closes and document properties are restored.",
            expected_active_application="Okna.exe",
            expected_window_title="Właściwości dokumentu",
        ),
    )
    return PreparedWindowHubFormAction(
        field_name=prepared.field_name,
        status=prepared.status,
        reason=prepared.reason,
        action=prepared.action,
        expected_outcome=prepared.expected_outcome,
        runtime_id=prepared.runtime_id,
        required_customer_name=customer_name,
    )
