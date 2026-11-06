"""Window construction learning on top of existing WindowHub demonstrations.

Only semantic control meaning, stage transitions and *presence* of changes.
Never capture customer values, window dimensions, catalog selections, prices,
native handles or coordinates as training material. No implied causal action.
"""
from __future__ import annotations

from collections.abc import Mapping

from app.agent.offers.windowhub_offer_form_map import (
    WINDOWHUB_OFFER_CONTROL_SPECS, WindowHubFormStep,
)

# Construction concepts, not assumptions about the selected manufacturer.
CONSTRUCTION_GROUPS = {
    "item_type": ("position", ("item_type_window", "quantity_input")),
    "dimensions": ("dimensions", ("width_1", "height_1")),
    "frame_system": ("basic_parameters", ("profile_system_picker", "profile_color")),
    "reinforcement": ("basic_parameters", ("reinforcement_category", "reinforcement_automatic")),
    "glazing": ("glazing", ("glazing_package", "spacer_frame", "spacer_frame_color")),
    "hardware": ("hardware", ("hardware_profile", "hardware_group", "locking_interval")),
}
# Observed catalog/UIA mapping does not yet establish these distinct construction
# operations. They must be demonstrated and mapped, not assumed from the name.
PENDING_CONSTRUCTION_GROUPS = (
    "frame_geometry", "sash_count_and_opening", "sash_profile",
    "mullion_transom_layout", "hardware_compatibility", "glass_thickness_limits",
)

_STAGE_TO_GROUPS = {}
for _group, (_stage, _fields) in CONSTRUCTION_GROUPS.items():
    _STAGE_TO_GROUPS.setdefault(_stage, []).append(_group)

_FIELDS_BY_STEP = {}
for _spec in WINDOWHUB_OFFER_CONTROL_SPECS:
    _FIELDS_BY_STEP.setdefault(_spec.step.value, set()).add(_spec.field_name)


def construction_map_coverage():
    """Report known UIA mapping separately from construction concepts still missing."""
    result = {}
    for group, (stage, fields) in CONSTRUCTION_GROUPS.items():
        matched = tuple(field for field in fields if field in _FIELDS_BY_STEP.get(stage, set()))
        result[group] = {
            "stage": stage,
            "mapped_fields": matched,
            "unmapped_fields": tuple(field for field in fields if field not in matched),
            "status": "uia_mapped_not_business_validated" if len(matched) == len(fields) else "mapping_incomplete",
        }
    return {
        "mapped_groups": result,
        "pending_groups": PENDING_CONSTRUCTION_GROUPS,
    }


def construction_demonstration_report(records):
    """Learn which construction screens and field *states* were demonstrated.

    The existing redacted demonstration records intentionally do not contain
    control values. Therefore this cannot learn specific profile selections,
    frame/sash topology, glazing Ug, dimensions, or catalog compatibility.
    """
    observed_stages = set()
    stage_transitions = set()
    observed_control_effects = set()
    for record in records:
        if not isinstance(record, Mapping) or record.get("type") != "transition":
            continue
        transition = record.get("transition")
        if not isinstance(transition, Mapping):
            continue
        before, after = transition.get("from_stage"), transition.get("to_stage")
        if isinstance(before, str) and before in _STAGE_TO_GROUPS:
            observed_stages.add(before)
        if isinstance(after, str) and after in _STAGE_TO_GROUPS:
            observed_stages.add(after)
        if isinstance(before, str) and isinstance(after, str) and before != after:
            if before in _STAGE_TO_GROUPS or after in _STAGE_TO_GROUPS:
                stage_transitions.add((before, after))
        # Labels are safe only if they match an explicit curated map spec.
        if before != after or before not in _STAGE_TO_GROUPS:
            continue
        # Labels shared by several native fields (e.g. width or color)
        # are ambiguous in a redacted demonstration, so do not attribute
        # their effects to any particular frame, glazing or hardware field.
        names_by_label = {}
        for spec in WINDOWHUB_OFFER_CONTROL_SPECS:
            if spec.step.value == before:
                names_by_label.setdefault(spec.label, set()).add(spec.field_name)
        safe_labels = {
            label: next(iter(fields))
            for label, fields in names_by_label.items() if len(fields) == 1
        }
        for change in (transition.get("changed") or [])[:20]:
            if not isinstance(change, Mapping):
                continue
            # New demonstrations supply an unambiguous curated field name.
            # Legacy recordings can still use a label only when the mapping
            # identifies exactly one field in this wizard stage.
            explicit = change.get("field_name")
            name = (explicit if isinstance(explicit, str)
                    and explicit in _FIELDS_BY_STEP[before]
                    else safe_labels.get(change.get("label")))
            if not name or name not in _FIELDS_BY_STEP[before]:
                continue
            old, new = change.get("before"), change.get("after")
            if not isinstance(old, Mapping) or not isinstance(new, Mapping):
                continue
            # Only effects (not values): a changed selection, toggle or nonempty status.
            for field in ("checked", "selected", "value_present"):
                if type(old.get(field)) is bool and type(new.get(field)) is bool:
                    if old[field] != new[field]:
                        observed_control_effects.add((before, name, field))
    groups = {}
    for group, (stage, fields) in CONSTRUCTION_GROUPS.items():
        demonstrated = tuple(sorted(
            f for f in fields
            if any(item[0] == stage and item[1] == f
                   for item in observed_control_effects)
        ))
        groups[group] = {
            "stage_observed": stage in observed_stages,
            "fields_with_observed_effect": demonstrated,
            "fields_not_yet_demonstrated": tuple(f for f in fields if f not in demonstrated),
            "semantic_only": True,
        }
    return {
        "construction_groups": groups,
        "observed_stage_transitions": tuple(sorted(stage_transitions)),
        "pending_construction_groups": PENDING_CONSTRUCTION_GROUPS,
        "catalog_compatibility_verified": False,
        "frame_sash_topology_learned": False,
    }


def construction_learning_experience(records, *, limit=8):
    """Small, sanitized experience for existing NaviMind V2 training context."""
    if not 1 <= limit <= 12:
        raise ValueError("construction_experience_limit_invalid")
    report = construction_demonstration_report(records)
    experience = []
    for group, status in report["construction_groups"].items():
        if not status["stage_observed"]:
            continue
        experience.append({
            "source": "windowhub_construction_demonstration",
            "construction_group": group,
            "stage": CONSTRUCTION_GROUPS[group][0],
            "observed_field_state_changes": list(status["fields_with_observed_effect"]),
            "certainty": "observed_ui_state_not_product_compatibility",
        })
        if len(experience) >= limit:
            break
    return tuple(experience)
