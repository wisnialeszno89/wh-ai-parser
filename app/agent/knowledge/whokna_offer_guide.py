"""Source-grounded, non-executing WH Okna offer planning.

Documentation is reference knowledge only. The planner never clicks, opens
documents, infers a dealer's available components, or declares a step done.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.run_navimind_find_learned_tool import find_candidates

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_PATH = ROOT / "knowledge" / "whokna_public_reference_v1.json"

STAGES = (
    ("document", "Utwórz dokument OFR i potwierdź dane klienta", None),
    ("position", "Dodaj pozycję, ilość i wymiary", None),
    ("frame", "Dobierz kombinację ościeżnica/skrzydło", "oscieznica"),
    ("verify_sash", "Sprawdź skrzydło wstawione według wybranego typu", "skrzydlo"),
    ("glazing", "Wybierz i sprawdź szklenie", "szklenie"),
    ("hardware", "Dobierz okucia i sprawdź kierunek otwierania", "okucia"),
    ("prices", "Sprawdź ustawienia prezentacji cen i kalkulację", None),
    ("review", "Zweryfikuj kompletną ofertę bez jej akceptowania", None),
)

RULE_IDS = {
    "document": ("offer_properties", "document_tabs"),
    "frame": ("frame", "component_variations", "profile_catalogue", "position_color"),
    "verify_sash": ("sash", "view_window"),
    "glazing": ("glazing", "component_variations", "glazing_catalogue"),
    "hardware": ("hardware", "hardware_limits", "view_window"),
    "position": ("offer_progression", "position_manager", "position_kind_quantity", "position_dimensions"),
    "prices": ("pricing_components", "dealer_price_view"),
    "review": ("document_lifecycle",),
}

MUTATING = {"document", "position", "frame", "glazing", "hardware", "prices"}


def load_reference(path: Path = KNOWLEDGE_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "navimind.whokna.reference_knowledge.v1":
        raise ValueError("unsupported_reference_schema")
    return data


def standard_tilt_turn_labels() -> tuple[str, ...]:
    policy = load_reference()["catalogue_policies"]["standard_tilt_turn"]
    labels = policy["exact_labels"]
    if not labels or not all(isinstance(label, str) and label.strip() for label in labels):
        raise ValueError("standard_tilt_turn_catalogue_labels_missing")
    return tuple(labels)


def single_sash_construction_recipe():
    """Bind documented concepts to the observed single-sash editor sequence."""
    from app.agent.learning.windowhub_builder_replay import NEXT_STEP
    from app.gui.enums.gui_tool import GuiTool

    rule_ids = {
        GuiTool.FRAME: ("frame",),
        GuiTool.SASH: ("sash",),
        GuiTool.GLASS: ("glazing",),
        GuiTool.HARDWARE: ("hardware", "hardware_limits"),
    }
    rules = {rule["id"]: rule for rule in load_reference()["rules"]}
    return {
        state: (tool, expected, tuple(rules[rule_id] for rule_id in rule_ids[tool]))
        for state, (tool, expected) in NEXT_STEP.items()
    }


def offer_plan(
    reference: dict,
    *,
    width: int,
    height: int,
    quantity: int = 1,
    glazing: str = "2-szybowy",
    outer_color: str = "antracyt",
    inner_color: str = "biały",
    icon_map: dict | None = None,
) -> dict:
    if not (300 <= width <= 5000 and 300 <= height <= 5000):
        raise ValueError("dimensions_outside_planning_guard")
    if not 1 <= quantity <= 100:
        raise ValueError("quantity_outside_planning_guard")
    rules = {rule["id"]: rule for rule in reference.get("rules", [])}
    mapped = bool(icon_map)
    if mapped and icon_map.get("schema") != "navimind.icon_map.unverified.v1":
        raise ValueError("unsupported_icon_map_schema")
    stages = []
    for key, title, concept in STAGES:
        matched = (find_candidates(icon_map, concept)[:2]
                   if mapped and concept else [])
        sources = [rules[rule_id] for rule_id in RULE_IDS.get(key, ())
                   if rule_id in rules]
        stages.append({
            "id": key,
            "title": title,
            "intent": concept,
            "source_rules": [
                {"id": rule["id"], "guidance": rule["guidance"],
                 "source_pages": rule.get("source_pages", [])}
                for rule in sources
            ],
            "tool_hypotheses": matched,
            "state": "not_started",
            "needs_runtime_verification": True,
            "requires_test_offer_for_write": key in MUTATING,
        })
    return {
        "schema": "navimind.whokna.guided_offer_plan.v1",
        "mode": "plan_only_no_desktop_actions",
        "request": {
            "width_mm": width, "height_mm": height, "quantity": quantity,
            "glazing": glazing, "outer_color": outer_color,
            "inner_color": inner_color,
        },
        "source": reference["source"],
        "stages": stages,
        "safety": {
            "all_steps_require_observation_and_postcondition": True,
            "ocr_is_not_click_authority": True,
            "manual_prepare_application": True,
            "forbid_zlc_order_mutation": True,
            "forbid_document_acceptance_or_send": True,
            "unknown_dealer_configuration_blocks_guessing": True,
        },
    }
