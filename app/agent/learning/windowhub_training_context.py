"""Curated domain knowledge + observed human demonstrations for NaviMind V2.

General computer interaction skills and WindowHub-specific labels are distinct.
The model can propose a next action, but only the local runtime may execute it.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.agent.learning.windowhub_demonstration import demonstration_experience, demonstration_summary
from app.agent.learning.windowhub_construction_learning import (
    construction_map_coverage, construction_demonstration_report,
    construction_learning_experience,
)


def _json_compatible_construction_map(value):
    """Convert static construction-mapping tuples to JSON arrays.

    The underlying coverage report intentionally uses immutable tuples for
    local consumers. NaviMind V2 accepts JSON lists, not Python tuples.
    Keep the transformation limited to this curated mapping; never loosen
    the V2 protocol validator for arbitrary objects.
    """
    if isinstance(value, dict):
        return {key: _json_compatible_construction_map(item)
                for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_compatible_construction_map(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError("windowhub_construction_map_contains_unsupported_type")


def windowhub_skill_knowledge() -> dict[str, object]:
    return {
        "application": "WindowHub",
        "general_computer_skills": [
            "Observe the current window before acting; an earlier screenshot may be stale.",
            "Find controls by role, human meaning, enabled state and stable UIA identity.",
            "Click opens dialogs, editable controls accept text, tabs change form steps.",
            "After every action compare observed state with the expected outcome.",
            "Do not interpret an action dispatch as a completed business task.",
            "If a screen differs, reconsider the plan; never repeat an unverified click.",
            "Understand form semantics: text input is an uncommitted query until a matching record is selected.",
            "Observe suggestion lists while typing; a dropdown may disappear when the complete text is entered.",
            "Selection is different from typing; click a uniquely matching suggestion, then verify the committed field.",
            "Treat Next/Dalej as navigation, OK/Zatwierdz as confirmation, Anuluj as cancellation, and plus as creation.",
            "Do not click OK or green plus simply because an earlier action failed; reason about the current state.",
            "Observe -> propose -> validate target -> act -> reobserve -> compare expected outcome -> correct or stop.",
            "If an accessibility tree misses a dropdown, use bounded screenshot OCR and corroborate geometry.",
            "If OCR recognizes the exact target but postcondition is unavailable, report a verification gap instead of guessing.",
            "Learn from the last action outcome, storing observed stage, selected control and failure cause; never store a guessed success.",
        ],
        "business_goal": "Create a WindowHub window offer from customer requirements.",
        "known_stages": [
            "start", "document_properties", "new_customer", "offer_document",
            "position", "dimensions", "basic_parameters", "glazing",
            "hardware", "modifier",
        ],
        "windowhub_semantics": [
            "From Start, NOWA OFERTA begins a new document.",
            "Document properties contain customer lookup, customer Add and price exclusions.",
            "Customer Add is different from choosing an existing customer.",
            "Overall window width/height are not the separate skos dimension fields.",
            "Profile color must match side-specific requirements, not only a substring.",
            "Zakończ may persist a business position; verify the modifier is reached.",
        ],
        "window_construction_learning": {
            "frame": "System profile and frame geometry must be verified from the actual catalog.",
            "sash": "Sash count, opening direction and sash profile are distinct from the frame.",
            "glazing": "Glass package, spacer and applicable thickness constraints are separate choices.",
            "hardware": "Hardware type, opening mode and compatibility must be verified against the chosen sash.",
            "policy": "A demonstrated screen state is not proof of a valid buildable configuration.",
        },
        "construction_ui_mapping": _json_compatible_construction_map(construction_map_coverage()),
        "uncertainties": [
            "The selected customer value may not be exposed by the native lookup.",
            "Multiple offers may be open; Cancel may leave the intended workflow.",
            "The color catalog and modifier require separate real-environment verification.",
        ],
    }


def read_demonstration_records(path: Path, *, max_bytes: int = 1_000_000) -> list[dict[str, object]]:
    """Read bounded local demo records, exposing only de-identified stage transitions."""
    if not isinstance(path, Path):
        raise TypeError("demonstration_path_required")
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError("demonstration_missing_or_too_large")
    records = []
    with path.open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if index >= 5_000:
                break
            try:
                item = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(item, dict):
                records.append(item)
    return records


def read_demonstration_experience(path: Path) -> tuple[dict[str, object], ...]:
    records = read_demonstration_records(path)
    # Keep within V2's 20-item experience limit, and retain stage learning.
    return (
        demonstration_experience(records, limit=12)
        + construction_learning_experience(records, limit=8)
    )


def read_demonstration_report(path: Path) -> dict[str, object]:
    records = read_demonstration_records(path)
    return {
        **demonstration_summary(records),
        "construction_learning": construction_demonstration_report(records),
    }
