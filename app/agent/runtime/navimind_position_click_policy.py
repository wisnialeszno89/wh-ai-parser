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
