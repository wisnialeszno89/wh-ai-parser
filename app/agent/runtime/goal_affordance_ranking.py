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


_NAVIGATION_NOISE = frozenset({
    "wiersz w gore", "wiersz w dol", "strona w gore", "strona w dol",
    "strona w lewo", "strona w prawo", "kolumna w gore", "kolumna w dol",
    "kolumna w lewo", "kolumna w prawo", "zaznacz wszystkie", ">>>", "<<<",
})


def _navigation_noise(label: str) -> bool:
    # Only a ranking penalty. Still available when the application has no
    # better relevant affordance, or when requested explicitly.
    ascii_label = unicodedata.normalize("NFKD", str(label).casefold())
    ascii_label = "".join(c for c in ascii_label if not unicodedata.combining(c))
    return " ".join(ascii_label.split()) in _NAVIGATION_NOISE


def affordance_relevance(affordance, *, goal: str, reference_map,
                         task_id: str, world_revision: int, panel_context=None):
    """Return inspectable evidence of ranking; never authorize execution."""
    if not isinstance(affordance, Mapping):
        return {"score": 0, "direct": 0, "context": 0, "label": ""}
    label, panel_bonus = "", 0
    ref = affordance.get("entity_ref")
    if isinstance(ref, str):
        try:
            element = reference_map.resolve(
                ref, task_id=task_id, world_revision=world_revision
            )
            label = ((element.metadata or {}).get("semantic_label")
                     or element.label or "")
            if panel_context is not None:
                from app.agent.runtime.active_panel_context import action_panel_priority
                panel_bonus = action_panel_priority(element, panel_context, goal=goal)
        except (KeyError, ValueError):
            pass
    direct = relevance_score(goal, label=str(label))
    if not direct:
        # Descriptions ("Click visible control...") are generated from
        # affordances; they cannot prove the widget's business meaning.
        description_score = 0
    else:
        description_score = min(2, relevance_score(
            goal, label="", description=str(affordance.get("description", ""))
        ))
    # Semantic relevance must outweigh incidental focus/selected-tab signals.
    # The same generic panel can contain unrelated tools and templates.
    score = 4 * direct + panel_bonus + description_score
    if _navigation_noise(str(label)) and not direct:
        score -= 25
    return {"score": score, "direct": direct, "context": panel_bonus, "label": str(label)}


def order_observed_affordances(affordances, *, goal: str, reference_map,
                               task_id: str, world_revision: int, panel_context=None):
    scored = []
    for index, affordance in enumerate(affordances):
        rank = affordance_relevance(
            affordance, goal=goal, reference_map=reference_map,
            task_id=task_id, world_revision=world_revision,
            panel_context=panel_context,
        )
        scored.append((-rank["score"], index, affordance))
    scored.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in scored]
