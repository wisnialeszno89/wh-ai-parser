"""Independent, exact UIA readback after one WindowHub text entry.

An execution return code is NOT proof that an edit persisted. A fresh scene
must still show the same live UIA runtime id, the mapped field and its value.
This deliberately does not claim construction completion or permission to save.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldReadback:
    verified: bool
    reason: str
    field_name: str = ""


def verify_written_field(
    scene, *, field_name: str, expected_value: str,
    expected_runtime_id: str, expected_stage: str,
) -> FieldReadback:
    from app.agent.learning.windowhub_demonstration import stage_of
    from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap

    if (not isinstance(field_name, str) or not field_name
            or not isinstance(expected_value, str)
            or not isinstance(expected_runtime_id, str)
            or not expected_runtime_id
            or expected_stage not in {"position", "dimensions"}):
        return FieldReadback(False, "readback_proof_arguments_invalid")
    try:
        if stage_of(scene) != expected_stage:
            return FieldReadback(False, "readback_wizard_stage_changed")
        snapshot = WindowHubOfferFormMap().inspect(scene)
        if snapshot is None:
            return FieldReadback(False, "readback_form_unavailable")
        field = snapshot.field(field_name)
        if field is None or not field.is_unique or field.element is None:
            return FieldReadback(False, "readback_field_not_unique")
        meta = field.element.metadata or {}
        if (meta.get("source") not in {
                "windowhub_ui_automation", "windows_ui_automation"}
                or meta.get("uia_visible") is not True
                or meta.get("uia_enabled") is not True
                or meta.get("uia_runtime_id") != expected_runtime_id):
            return FieldReadback(False, "readback_uia_identity_changed")
        value = meta.get("current_value")
        if (not isinstance(value, str)
                or meta.get("current_value_source") is None):
            return FieldReadback(False, "readback_native_value_missing")
        if value.strip() != expected_value.strip():
            return FieldReadback(False, "readback_value_mismatch")
        return FieldReadback(True, "fresh_native_uia_value_verified", field_name)
    except (ValueError, TypeError, AttributeError, KeyError):
        return FieldReadback(False, "readback_observation_unreadable")
