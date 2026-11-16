"""Read-only structural understanding of active panels inside one UIA window.

Uses UIA parent relationships, focus and selected tabs, not guessed button
coordinates. This evidence helps rank controls; it never authorizes actions.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

_UIA = frozenset({"windows_ui_automation", "windowhub_ui_automation"})
_GROUP_ROLES = frozenset({
    "pane", "group", "tab", "tabitem", "window", "dialog",
    "custom", "toolbar", "table", "datagrid",
})


def _clean(value) -> str:
    return " ".join(value.strip().split())[:120] if isinstance(value, str) else ""


def _ancestry(element) -> tuple:
    entries = (element.metadata or {}).get("uia_ancestor_context", ())
    return entries if isinstance(entries, (tuple, list)) else ()


def panel_lineage(element) -> tuple[str, ...]:
    """Return names of structural containers from nearest parent outward."""
    result = []
    for item in _ancestry(element)[:12]:
        if isinstance(item, (tuple, list)) and len(item) >= 3:
            role, _cls, name = item[:3]
        elif isinstance(item, dict):
            role = item.get("control_type")
            name = item.get("name")
        else:
            continue
        role = _clean(role).casefold()
        name = _clean(name)
        if role in _GROUP_ROLES and name and name.casefold() not in {
            "oknawpf", "layoutcontrol", "part_item",
        } and name not in result:
            result.append(name)
    return tuple(result[:8])


@dataclass(frozen=True)
class PanelContext:
    status: str
    selected_tabs: tuple[str, ...]
    focused_labels: tuple[str, ...]
    panel_labels: tuple[str, ...]
    contextual_controls: int
    all_controls: int
    focused_containers: tuple[str, ...] = ()


def observe_panel_context(scene) -> PanelContext:
    controls = [
        e for e in getattr(scene, "elements", ())
        if (e.metadata or {}).get("source") in _UIA
        and (e.metadata or {}).get("uia_visible") is True
    ]
    selected = tuple(dict.fromkeys(
        _clean(e.label) for e in controls
        if e.kind == "tabitem" and (e.metadata or {}).get("uia_selected") is True
        and _clean(e.label)
    ))[:8]
    focused = tuple(dict.fromkeys(
        _clean(e.label) for e in controls
        if (e.metadata or {}).get("uia_focused") is True and _clean(e.label)
    ))[:8]
    counts = Counter(
        label for e in controls for label in panel_lineage(e)
    )
    panel_labels = tuple(k for k, _ in counts.most_common(8))
    scoped = sum(bool(panel_lineage(e)) for e in controls)
    focused_containers = tuple(dict.fromkeys(
        name for e in controls
        if (e.metadata or {}).get("uia_focused") is True
        for name in panel_lineage(e)
    ))[:8]
    if not controls:
        status = "no_accessible_controls"
    elif len(selected) == 1:
        status = "selected_tab_observed"
    elif focused:
        status = "focus_observed_no_unique_selected_tab"
    elif panel_labels:
        status = "group_structure_observed_without_active_marker"
    else:
        status = "unscoped_controls_only"
    return PanelContext(
        status, selected, focused, panel_labels, scoped, len(controls),
        focused_containers,
    )


def action_panel_priority(element, context: PanelContext, *, goal: str = "") -> int:
    """Contextual preference, not proof of the correct business target."""
    from app.agent.runtime.goal_affordance_ranking import relevance_score
    meta = element.metadata or {}
    if meta.get("source") not in _UIA or meta.get("uia_visible") is not True:
        return 0
    lineage = panel_lineage(element)
    bonus = max((relevance_score(goal, label=name) for name in lineage), default=0)
    if (meta.get("uia_focused") is True):
        bonus += 7
    if len(context.selected_tabs) == 1 and context.selected_tabs[0] in lineage:
        bonus += 12
    if context.focused_containers and any(
        parent in context.focused_containers for parent in lineage
    ):
        bonus += 8
    # Never equate an unrelated selected tab with a label from a different
    # UIA tree or infer that a panel is active from its mere visibility.
    return bonus


_SAFE_AREA_TERMS = {
    "start1": "start",
    "wielkosc okna": "dimensions",
    "parametry szklenia": "glazing",
    "konstrukcja": "construction",
    "modyfikator": "construction_editor",
    "szablony wydrukow": "print_templates",
    "wydruki": "print_templates",
    "podglad wydruku": "print_preview",
    "wlasciwosci dokumentu": "document_properties",
}


def _safe_area(label: str) -> str | None:
    from app.agent.runtime.goal_affordance_ranking import normalize_words
    joined = " ".join(sorted(normalize_words(label)))
    for phrase, category in _SAFE_AREA_TERMS.items():
        if joined == " ".join(sorted(normalize_words(phrase))):
            return category
    return None


def panel_model_context(scene) -> dict:
    """Model-facing categorization without arbitrary customer/project titles."""
    ctx = observe_panel_context(scene)
    return {
        "source": "local_uia_structure",
        "verification": "observed_not_authorizing",
        "selected_areas": sorted({
            tag for name in ctx.selected_tabs
            if (tag := _safe_area(name)) is not None
        }),
        "visible_area_categories": sorted({
            tag for name in ctx.panel_labels
            if (tag := _safe_area(name)) is not None
        }),
        "focused_widget_present": bool(ctx.focused_labels),
        "focused_area_categories": sorted({
            tag for name in ctx.focused_containers
            if (tag := _safe_area(name)) is not None
        }),
        "active_area_confidence": (
            "selected_tab" if len(ctx.selected_tabs) == 1
            else "focused_control" if ctx.focused_labels
            else "unknown"
        ),
    }


def safe_panel_diagnostics(scene) -> dict:
    context = observe_panel_context(scene)
    # Avoid printing raw labels: panels can be named after customer projects.
    return {
        "context_status": context.status,
        "selected_tab_count": len(context.selected_tabs),
        "focused_control_count": len(context.focused_labels),
        "named_container_count": len(context.panel_labels),
        "controls_with_ancestry": context.contextual_controls,
        "accessible_controls": context.all_controls,
    }
