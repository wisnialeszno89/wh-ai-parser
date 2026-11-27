"""Allowlisted navigation for multi-position WindowHub draft missions.

Only semantic controls whose identities are proven by native V2/UIA can
change the current wizard step. Catalogue picks and finalization require a
separately learned and independently verified skill, not model confidence.
"""
from __future__ import annotations


def allowed_position_click(
    *, stage: str, target, current_position, field_receipts=(),
) -> tuple[bool, str]:
    if current_position is None:
        return False, "active_position_missing"
    if getattr(current_position, "product_type", None) != "window":
        return False, "product_type_not_supported_by_pilot"
    label = " ".join(str(getattr(target, "label", "") or "").casefold().split())
    role = str(getattr(target, "role", "") or "").casefold()
    automation_id = getattr(target, "automation_id", None)
    position_id = current_position.position_id
    proven = {
        item.field_name for item in field_receipts
        if item.position_id == position_id
        and item.value and item.signature
    }
    if (stage == "offer_document" and role == "button"
            and label == "dodaj"):
        # The original native MDI ownership check is still mandatory.
        return True, "native_offer_add_requires_mdi_proof"
    if (stage == "position" and role == "radiobutton"
            and label == "okno" and automation_id == "1329"):
        return True, "window_item_type_from_current_position"
    next_button = (
        role == "button" and label == "dalej >"
        and automation_id == "12324"
    )
    if next_button and stage == "position":
        if "quantity_input" in proven:
            return True, "quantity_readback_before_next"
        return False, "quantity_readback_missing_before_next"
    if next_button and stage == "dimensions":
        if {"width_1", "height_1"}.issubset(proven):
            return True, "dimensions_readback_before_next"
        return False, "dimensions_readback_missing_before_next"
    return False, "catalogue_or_unknown_wizard_click_requires_learning"


def verify_position_navigation_readback(
    scene, *, stage: str, target, current_position,
    field_receipts=(),
) -> tuple[bool, str]:
    """On Next, re-read required live fields BEFORE any native action."""
    allowed, reason = allowed_position_click(
        stage=stage, target=target,
        current_position=current_position,
        field_receipts=field_receipts,
    )
    receipt_only_blockers = {
        "quantity_readback_missing_before_next",
        "dimensions_readback_missing_before_next",
    }
    if not allowed and reason not in receipt_only_blockers:
        return False, reason
    label = " ".join(str(getattr(target, "label", "") or "").casefold().split())
    if label != "dalej >":
        return (True, reason) if allowed else (False, reason)
    required = {
        "position": {"quantity_input": current_position.quantity},
        "dimensions": {
            "width_1": current_position.width_mm,
            "height_1": current_position.height_mm,
        },
    }.get(stage)
    if (required is None or
            any(type(value) is not int or value <= 0
                for value in required.values())):
        return False, "active_position_values_missing_for_navigation"
    from app.agent.runtime.navimind_field_readback import (
        verify_written_field,
    )
    from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
    snapshot = WindowHubOfferFormMap().inspect(scene)
    if snapshot is None:
        return False, "native_wizard_form_unavailable"
    for field_name, requested in required.items():
        field = snapshot.field(field_name)
        if field is None or not field.is_unique or field.element is None:
            return False, "native_field_missing_before_next_" + field_name
        runtime_id = (field.element.metadata or {}).get("uia_runtime_id")
        matching = [
            r for r in field_receipts
            if r.position_id == current_position.position_id
            and r.field_name == field_name
        ]
        if len(matching) > 1:
            return False, "duplicate_field_receipts_before_next"
        if matching:
            # A previously proved field must still have the same native
            # identity and source value. It may not be reused after a change.
            item = matching[0]
            if (item.value != str(requested)
                    or item.runtime_id != runtime_id):
                return False, "stale_field_receipt_before_next_" + field_name
        proof = verify_written_field(
            scene, field_name=field_name,
            expected_value=str(requested),
            expected_runtime_id=runtime_id,
            expected_stage=stage,
        )
        if not proof.verified:
            return False, "live_field_mismatch_before_next_" + field_name
    return True, "all_required_native_fields_fresh_and_match_source"
