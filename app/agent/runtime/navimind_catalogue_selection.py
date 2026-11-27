"""Fail-closed exact UIA catalogue selection from verified source facts.

Supports ONLY list items native-ancestor-bound to one mapped combo. A separate
popup without verifiable parent remains unsupported until demonstrated.
No fuzzy names, no SQL, no invented catalogue variants, no automatic save.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CataloguePick:
    position_id: str
    stage: str
    field_name: str
    expected_value: str
    combobox_runtime_id: str
    option_runtime_id: str


# Mapping is deliberately narrow; hardware_group and profile-system modal
# are NOT assumed to be the same as a basic profile colour dropdown.
_FIELD_REQUIREMENTS = {
    "basic_parameters": (
        ("profile_color", "same_inside_outside"),
    ),
    "glazing": (
        ("glazing_package", "glazing"),
        ("spacer_frame", "spacer"),
    ),
    "hardware": (
        ("hardware_profile", "hardware"),
    ),
}


def _exact_text(text: str) -> str:
    return " ".join(text.casefold().split())


def requested_exact_value(position, request_key: str) -> str | None:
    values = dict(getattr(position, "catalogue_requirements", ()) or ())
    if request_key == "same_inside_outside":
        inside, outside = values.get("color_inside"), values.get("color_outside")
        return inside if inside and outside and _exact_text(inside) == _exact_text(outside) else None
    value = values.get(request_key)
    return value if isinstance(value, str) and value.strip() else None


def verify_catalogue_dropdown_target(scene, position, target) -> bool:
    """Only open a mapped, uniquely identified dropdown requested by this row."""
    from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap

    snapshot = WindowHubOfferFormMap().inspect(scene)
    runtime_id = getattr(target, "uia_runtime_id", None)
    if snapshot is None or not runtime_id or getattr(target, "role", None) != "combobox":
        return False
    matches = []
    for field_name, request_key in _FIELD_REQUIREMENTS.get(snapshot.step.value, ()):
        if not requested_exact_value(position, request_key):
            continue
        match = snapshot.field(field_name)
        if match is None or not match.is_unique or match.element is None:
            continue
        element = match.element
        metadata = element.metadata or {}
        if (element.kind == "combobox" and metadata.get("uia_runtime_id") == runtime_id
                and metadata.get("uia_enabled") is True
                and metadata.get("uia_visible") is True
                and metadata.get("source") in {
                    "windows_ui_automation", "windowhub_ui_automation",
                }):
            matches.append(match)
    return len(matches) == 1


def prepare_exact_catalogue_pick(
    scene, position, target,
) -> tuple[CataloguePick | None, str]:
    """Read only. A model-proposed list click cannot invent an option."""
    from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
    snapshot = WindowHubOfferFormMap().inspect(scene)
    if (snapshot is None or position is None
            or position.product_type != "window"):
        return None, "catalogue_current_wizard_or_position_unverified"
    stage = snapshot.step.value
    permitted = _FIELD_REQUIREMENTS.get(stage, ())
    if not permitted or getattr(target, "role", "") != "listitem":
        return None, "catalogue_stage_or_option_role_not_supported"
    rid = getattr(target, "uia_runtime_id", None)
    label = getattr(target, "label", None)
    if not isinstance(rid, str) or not rid or not isinstance(label, str) or not label.strip():
        return None, "catalogue_option_target_missing_native_identity"
    options = [
        e for e in scene.elements
        if (e.kind == "listitem"
            and e.label == label
            and (e.metadata or {}).get("uia_runtime_id") == rid
            and (e.metadata or {}).get("source") in {
                "windows_ui_automation", "windowhub_ui_automation"
            }
            and (e.metadata or {}).get("uia_visible") is True
            and (e.metadata or {}).get("uia_enabled") is True)
    ]
    if len(options) != 1:
        return None, "catalogue_option_not_uniquely_observed"
    option = options[0]
    ancestry = (option.metadata or {}).get("uia_ancestor_runtime_structure")
    if not isinstance(ancestry, (tuple, list)):
        return None, "catalogue_dropdown_parent_unverified"
    candidates = []
    for field_name, request_key in permitted:
        expected = requested_exact_value(position, request_key)
        if not expected or _exact_text(label) != _exact_text(expected):
            continue
        match = snapshot.field(field_name)
        if match is None or not match.is_unique or match.element is None:
            continue
        field_meta = match.element.metadata or {}
        combo_runtime = field_meta.get("uia_runtime_id")
        combo_automation = field_meta.get("automation_id")
        if (match.element.kind != "combobox"
                or not isinstance(combo_runtime, str) or not combo_runtime
                or not isinstance(combo_automation, str) or not combo_automation
                or field_meta.get("uia_enabled") is not True):
            continue
        parents = [
            node for node in ancestry
            if isinstance(node, dict)
            and node.get("control_type") == "combobox"
            and node.get("automation_id") == combo_automation.casefold()
            and node.get("runtime_id") == combo_runtime
        ]
        if len(parents) != 1:
            continue
        candidates.append(CataloguePick(
            position_id=position.position_id, stage=stage,
            field_name=field_name, expected_value=expected,
            combobox_runtime_id=combo_runtime, option_runtime_id=rid,
        ))
    if len(candidates) != 1:
        return None, "catalogue_exact_match_or_dropdown_owner_unverified"
    return candidates[0], "exact_source_option_with_native_dropdown_parent"


def verify_exact_catalogue_readback(scene, pick: CataloguePick) -> tuple[bool, str]:
    """After click, independently observe selected combo value; never trust click."""
    from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
    snapshot = WindowHubOfferFormMap().inspect(scene)
    if snapshot is None or snapshot.step.value != pick.stage:
        return False, "catalogue_post_selection_stage_not_verified"
    match = snapshot.field(pick.field_name)
    if match is None or not match.is_unique or match.element is None:
        return False, "catalogue_post_selection_field_missing"
    metadata = match.element.metadata or {}
    if (metadata.get("uia_runtime_id") != pick.combobox_runtime_id
            or metadata.get("uia_visible") is not True
            or metadata.get("uia_enabled") is not True
            or metadata.get("current_value_source") not in {
                "get_value", "selected_text", "value", "legacy_value",
            }):
        return False, "catalogue_post_selection_native_identity_or_value_unverified"
    value = metadata.get("current_value")
    if not isinstance(value, str) or _exact_text(value) != _exact_text(pick.expected_value):
        return False, "catalogue_post_selection_value_mismatch"
    return True, "source_bound_native_catalogue_roundtrip_verified"
