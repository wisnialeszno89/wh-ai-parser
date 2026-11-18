"""Evidence-based scoping of duplicate controls in multiple WindowHub offers.

A selected document tab proves *which document* is active. It does not prove
that a toolbar button in a sibling MDI subtree belongs to that document.
Controls without established document_scope remain ambiguous.
"""
from __future__ import annotations


_UIA = frozenset({"windows_ui_automation", "windowhub_ui_automation"})


def selected_document_tab(scene) -> tuple[str | None, str]:
    tabs = [
        element for element in scene.elements
        if element.kind == "tabitem"
        and (element.metadata or {}).get("source") in _UIA
        and (element.metadata or {}).get("uia_tab_scope") == "document"
        and (element.metadata or {}).get("uia_visible") is True
        and (element.metadata or {}).get("uia_selected") is True
    ]
    if len(tabs) != 1:
        return None, "no_unique_selected_document_tab"
    name = (tabs[0].label or "").strip()
    return (name, "verified_selected_document_tab") if name else (None, "unnamed_selected_document_tab")


def control_document_scope(element, selected_tab: str | None) -> str:
    scope = (element.metadata or {}).get("document_scope")
    if not isinstance(scope, str) or not scope.strip():
        return "unknown"
    if not selected_tab:
        return "unknown"
    return "active" if scope.strip().casefold() == selected_tab.strip().casefold() else "other"


def duplicate_document_action_status(scene, *, label: str = "Dodaj") -> dict:
    from app.agent.runtime.active_panel_context import panel_lineage
    candidates = [
        e for e in scene.elements
        if e.kind == "button"
        and (e.label or "").strip().casefold() == label.casefold()
        and (e.metadata or {}).get("source") in _UIA
        and (e.metadata or {}).get("uia_visible") is True
        and (e.metadata or {}).get("uia_enabled") is True
        and not any("szablon" in p.casefold() or "wydruk" in p.casefold()
                    for p in panel_lineage(e))
    ]
    selected, selection_status = selected_document_tab(scene)
    statuses = [control_document_scope(e, selected) for e in candidates]
    unique_active = len(candidates) >= 1 and statuses.count("active") == 1 and statuses.count("unknown") == 0
    return {
        "observed": len(candidates),
        "selected_document_status": selection_status,
        "active_scope_proven": statuses.count("active"),
        "unresolved_scope": statuses.count("unknown"),
        "other_document_scope": statuses.count("other"),
        "safe_unique_active_target": bool(unique_active),
    }


def unique_active_document_control(scene, *, label: str = "Dodaj"):
    """Return unique verified document-scoped button; None if any ambiguity."""
    from app.agent.runtime.active_panel_context import panel_lineage
    selected, _ = selected_document_tab(scene)
    if not selected:
        return None
    candidates = [
        e for e in scene.elements
        if e.kind == "button"
        and (e.label or "").strip().casefold() == label.casefold()
        and (e.metadata or {}).get("source") in _UIA
        and (e.metadata or {}).get("uia_visible") is True
        and (e.metadata or {}).get("uia_enabled") is True
        and not any("szablon" in p.casefold() or "wydruk" in p.casefold()
                    for p in panel_lineage(e))
    ]
    if not candidates or any(control_document_scope(e, selected) == "unknown" for e in candidates):
        return None
    in_active = [e for e in candidates if control_document_scope(e, selected) == "active"]
    # Treat an explicitly verified global toolbar as excluded only when the
    # single active control is itself backed by native MDI ancestry.
    if any((e.metadata or {}).get("document_scope_source") == "verified_outside_mdi"
           for e in candidates):
        if len(in_active) != 1 or (in_active[0].metadata or {}).get(
            "document_scope_source"
        ) != "verified_native_mdi_child":
            return None
    return in_active[0] if len(in_active) == 1 else None
