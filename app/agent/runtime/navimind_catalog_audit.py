"""Read-only catalogue UIA accessibility audit for WindowHub.

Do not infer available SQL catalogue choices from the presence of a combobox.
Never mutate a field, open a dropdown, or claim that a value can be selected.
The report intentionally contains no customer names or selected option values.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.agent.offers.windowhub_offer_form_map import (
    WindowHubOfferFormMap,
)

CATALOG_FIELD_GROUPS = {
    "profiles_and_colors": (
        "profile_system_picker", "profile_color", "reinforcement_category",
    ),
    "glazing": (
        "glazing_package", "glazing_details", "spacer_frame", "spacer_frame_color",
    ),
    "hardware": (
        "hardware_profile", "hardware_group", "hardware_inner_color",
        "hardware_outer_color", "backset", "rebate_type",
        "faceplate_strip", "handle_spindle_length_selector",
    ),
}


@dataclass(frozen=True)
class CatalogFieldAudit:
    field_name: str
    group: str
    state: str
    native_value_available: bool
    unique_runtime_id: bool
    option_inventory_verified: bool = False
    selection_roundtrip_verified: bool = False


@dataclass(frozen=True)
class CatalogAudit:
    stage: str
    fields: tuple[CatalogFieldAudit, ...]
    safe_observation: bool
    notes: tuple[str, ...]

    def safe_summary(self) -> dict:
        counts = {}
        for field in self.fields:
            counts[field.state] = counts.get(field.state, 0) + 1
        return {
            "stage": self.stage,
            "safe_observation": self.safe_observation,
            "field_counts": counts,
            "fields": [
                {
                    "field_name": f.field_name,
                    "group": f.group,
                    "state": f.state,
                    "native_value_available": f.native_value_available,
                    "unique_runtime_id": f.unique_runtime_id,
                    "option_inventory_verified": f.option_inventory_verified,
                    "selection_roundtrip_verified": f.selection_roundtrip_verified,
                }
                for f in self.fields
            ],
            "notes": list(self.notes),
            "read_only": True,
            "database_queried": False,
            "catalogue_selection_executed": False,
        }


def audit_catalogue_scene(scene) -> CatalogAudit:
    """Inspect *only* the current WindowHub wizard screen.

    No list expansion or data extraction; selection capability remains
    unverified until an actual consented local UIA dropdown roundtrip.
    """
    mapping = WindowHubOfferFormMap()
    snapshot = mapping.inspect(scene)
    if snapshot is None:
        return CatalogAudit(
            "unknown", (), False,
            ("windowhub_catalogue_wizard_not_verified",),
        )
    wanted = {
        field: group
        for group, names in CATALOG_FIELD_GROUPS.items()
        for field in names
    }
    visible = []
    counts = {}
    for element in scene.elements:
        metadata = element.metadata or {}
        runtime = metadata.get("uia_runtime_id")
        if (metadata.get("source") in {
                "windowhub_ui_automation", "windows_ui_automation"}
                and isinstance(runtime, str) and runtime):
            counts[runtime] = counts.get(runtime, 0) + 1

    for name, group in wanted.items():
        spec = mapping.spec_for_field(name)
        if spec is None or spec.step != snapshot.step:
            continue
        field = snapshot.field(name)
        if field is None or not field.is_unique or field.element is None:
            state = "missing_or_ambiguous"
            value_present = False
            runtime_unique = False
        else:
            meta = field.element.metadata or {}
            runtime = meta.get("uia_runtime_id")
            runtime_unique = (
                isinstance(runtime, str) and bool(runtime)
                and counts.get(runtime) == 1
            )
            if meta.get("uia_enabled") is not True or not runtime_unique:
                state = "present_not_verified"
            else:
                state = "control_identified"
            value_present = (
                state == "control_identified"
                and isinstance(meta.get("current_value"), str)
                and bool(meta.get("current_value").strip())
                and bool(meta.get("current_value_source"))
            )
        visible.append(CatalogFieldAudit(
            field_name=name, group=group, state=state,
            native_value_available=value_present,
            unique_runtime_id=runtime_unique,
        ))
    return CatalogAudit(
        snapshot.step.value, tuple(visible), True,
        (
            "native_controls_not_the_catalogue_database",
            "dropdown_options_not_enumerated",
            "no_catalogue_selection_roundtrip_implemented",
            "specific_installed_supplier_database_must_be_tested_locally",
        ),
    )
