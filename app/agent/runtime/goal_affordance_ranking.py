"""Relevance-based UI capability ordering for natural-language computer use.

This only ranks already *observed and locally permitted* controls. It never
authorizes a click, invents a widget, or decides an action is successful.
Every available capability remains accessible unless the strict request
budget is exhausted.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping

_STOP = frozenset({
    "i", "a", "z", "w", "na", "do", "dla", "oraz", "czy", "jak", "ale",
    "ze", "bez", "nie", "ma", "mam", "jest", "bede", "tylko", "teraz",
    "and", "the", "for", "with", "from", "into",
})

# Domain vocabulary maps *meaning*, not paths or screen sequences.
_CONCEPT_ALIASES = {
    "wymiar": ("szerokosc", "wysokosc", "rozmiar"),
    "szerokosc": ("width", "wymiar"),
    "wysokosc": ("height", "wymiar"),
    "kolor": ("barwa", "profile", "profil"),
    "szyb": ("szklenie", "pakiet", "glazing"),
    "okno": ("okien", "konstrukcja"),
    "oferta": ("dokument", "ofert"),
}


def normalize_words(value: str) -> set[str]:
    if not isinstance(value, str):
        return set()
    raw = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return {x for x in re.findall(r"[a-z0-9]{3,}", plain) if x not in _STOP}


def relevance_score(goal: str, *, label: str, description: str = "") -> int:
    wanted = normalize_words(goal)
    if not wanted:
        return 0
    expanded = set(wanted)
    for key, extras in _CONCEPT_ALIASES.items():
        if any(w == key or w.startswith(key) for w in wanted):
            expanded.update(extras)
    shown = normalize_words(label)
    described = normalize_words(description)
    exact = wanted & shown
    related = expanded & shown
    text_intersection = wanted & described
    # Exact label coincidence outranks generic action descriptions.
    return 10 * len(exact) + 5 * len(related - exact) + len(text_intersection)


def order_observed_affordances(affordances, *, goal: str, reference_map,
                               task_id: str, world_revision: int):
    scored = []
    for index, affordance in enumerate(affordances):
        if not isinstance(affordance, Mapping):
            scored.append((0, index, affordance))
            continue
        label = ""
        ref = affordance.get("entity_ref")
        if isinstance(ref, str):
            try:
                element = reference_map.resolve(
                    ref, task_id=task_id, world_revision=world_revision
                )
                label = (
                    (element.metadata or {}).get("semantic_label")
                    or element.label or ""
                )
            except (KeyError, ValueError):
                pass
        score = relevance_score(
            goal, label=str(label),
            description=str(affordance.get("description", "")),
        )
        scored.append((-score, index, affordance))
    scored.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in scored]
