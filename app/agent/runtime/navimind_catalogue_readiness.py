"""Read-only, non-invasive audit of real WH Okna catalogue selectors.

Mapping an accessible combobox is NOT proof that its underlying producer
database, list items, SQL rows, selection mechanics or resulting business
configuration can be reached. The report deliberately withholds option
names, prices, customer details, HWNDs and server identifiers.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

CATEGORIES = {
    "profile_and_color": ("profile_system_picker", "profile_color",
                          "reinforcement_category"),
    "glazing": ("glazing_package", "glazing_details", "spacer_frame",
                "spacer_frame_color"),
    "hardware": ("hardware_profile", "hardware_group",
                 "hardware_inner_color", "hardware_outer_color",
                 "locking_interval", "backset", "rebate_type"),
    "sill": ("sill_type", "sill_color", "sill_endcap"),
}


@dataclass(frozen=True)
class CatalogueControlStatus:
    field_name: str
    state: str
    native_value_readable: bool = False
    native_value_present: bool = False
    choice_items_independently_observed: bool = False
    safe_to_select: bool = False


@dataclass(frozen=True)
class CatalogueReadiness:
    stage: str
    status: str
    controls: tuple[CatalogueControlStatus, ...]
    scene_fingerprint: str = ""

    @property
    def selection_verified(self) -> bool:
        return False  # Never infer executable rights from read-only mapping.


def inspect_catalogue_scene(scene: Any) -> CatalogueReadiness:
    """Audit exact CURRENT UIA wizard scene without any click or enumeration.

    A dropdown that has not been opened by the salesperson cannot be
    advertised as an enumerated product catalogue.
    """
    from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
    from app.agent.perception.screen_scene import ScreenScene

    if not isinstance(scene, ScreenScene):
        return CatalogueReadiness("unknown", "not_a_screen_scene", ())
    try:
        mapper = WindowHubOfferFormMap()
        snapshot = mapper.inspect(scene)
        if snapshot is None:
            return CatalogueReadiness("unknown", "catalogue_wizard_not_foreground", ())
        relevant = [
            field for fields in CATEGORIES.values()
            for field in fields
            if mapper.spec_for_field(field) is not None
            and mapper.spec_for_field(field).step == snapshot.step
        ]
        entries: list[CatalogueControlStatus] = []
        digest: list[tuple[str, str, str]] = []
        for name in relevant:
            field = snapshot.field(name)
            if field is None or not field.is_unique or field.element is None:
                state = "ambiguous" if field and field.status == "ambiguous" else "not_found"
                entries.append(CatalogueControlStatus(name, state))
                continue
            element = field.element
            metadata = element.metadata or {}
            runtime_id = metadata.get("uia_runtime_id")
            native = (
                metadata.get("source") in {
                    "windowhub_ui_automation", "windows_ui_automation"
                } and metadata.get("uia_visible") is True
                and metadata.get("uia_enabled") is True
                and isinstance(runtime_id, str) and bool(runtime_id.strip())
            )
            value = metadata.get("current_value")
            value_source = metadata.get("current_value_source")
            readable = native and isinstance(value, str) and bool(value_source)
            entries.append(CatalogueControlStatus(
                field_name=name,
                state=("mapped_native_unique" if native else
                       "mapped_but_native_identity_unverified"),
                native_value_readable=bool(readable),
                native_value_present=bool(readable and value.strip()),
                choice_items_independently_observed=False,
                safe_to_select=False,
            ))
            if native:
                digest.append((name, str(runtime_id), str(value or "")))
        # Hash only: never place proprietary catalogue selections in model chat.
        fingerprint = sha256(repr(tuple(digest)).encode("utf-8")).hexdigest()[:16]
        return CatalogueReadiness(
            snapshot.step.value,
            "mapped_controls_only_catalogue_choices_not_verified",
            tuple(entries),
            fingerprint,
        )
    except (AttributeError, TypeError, ValueError, KeyError):
        return CatalogueReadiness("unknown", "catalogue_audit_unreadable", ())


def summarize_catalogue_readiness(audit: CatalogueReadiness) -> str:
    """Bounded non-sensitive summary for a local operator or chat."""
    mapped = sum(c.state == "mapped_native_unique" for c in audit.controls)
    readable = sum(c.native_value_readable for c in audit.controls)
    missing = sum(c.state == "not_found" for c in audit.controls)
    ambiguous = sum(c.state == "ambiguous" for c in audit.controls)
    return (
        f"KATALOG_WH_STAGE={audit.stage}; STATUS={audit.status}; "
        f"FIELDS={len(audit.controls)}; NATIVE_MAPPED={mapped}; "
        f"CURRENT_SELECTION_READABLE={readable}; "
        f"MISSING={missing}; AMBIGUOUS={ambiguous}; "
        "CATALOGUE_ITEMS_ENUMERATED=False; "
        "CATALOGUE_SELECTION_EXECUTABLE=False; "
        "SCENE_PII_EXPORTED=False"
    )[:600]
