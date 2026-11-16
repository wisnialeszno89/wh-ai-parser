"""Read-only MDI ancestry probe for WindowHub's duplicate toolbar buttons.

The ordinary UIA document_scope is often None because an MDI content panel
is NOT inside its document TabItem. Diagnose the native Win32 child-window
chain instead. Never click and never infer ownership from button order.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter


@dataclass(frozen=True)
class MdiProbe:
    observed_buttons: int
    selected_document_verified: bool
    scope_candidates: tuple[str, ...]
    native_caption_matches: tuple[int, ...]
    native_distinct_roots: int
    unknown_buttons: int
    status: str


def native_title_matches(selected_name: str, title: str) -> bool:
    """Exact normalized MDI child title; no substring / order matching."""
    return bool(
        selected_name and title
        and selected_name.strip().casefold() == title.strip().casefold()
    )


def classify_native_candidates(*, selected_document: str | None,
                               candidate_ancestor_titles: tuple[tuple[str, ...], ...]) -> MdiProbe:
    matched = []
    unknown = 0
    for titles in candidate_ancestor_titles:
        matching = sum(native_title_matches(selected_document or "", title) for title in titles)
        matched.append(matching)
        if matching != 1:
            unknown += 1
    safe = (
        bool(selected_document)
        and unknown == 0
        and sum(value == 1 for value in matched) == 1
    )
    return MdiProbe(
        observed_buttons=len(candidate_ancestor_titles),
        selected_document_verified=bool(selected_document),
        scope_candidates=tuple("matching_mdi_ancestor" if x == 1 else "unresolved" for x in matched),
        native_caption_matches=tuple(matched),
        native_distinct_roots=0,
        unknown_buttons=unknown,
        status="candidate_for_structural_validation" if safe else "native_mdi_scope_unresolved",
    )


def inspect_native_mdi_button_ancestry(scene, *, desktop=None, limit=8) -> dict:
    """Read-only Win32 + UIA probe for observed duplicate 'Dodaj' controls.

    Return *counts*, ancestor role/class signatures and exact title-match
    booleans; no HWND, business text, screenshots or raw captions.
    """
    import os
    if os.name != "nt" and desktop is None:
        return {"status": "windows_required"}
    from app.agent.runtime.active_document_scope import selected_document_tab
    from app.agent.runtime.active_panel_context import panel_lineage
    selected, tab_status = selected_document_tab(scene)
    observations = [
        e for e in scene.elements
        if e.kind == "button"
        and (e.label or "").strip().casefold() == "dodaj"
        and (e.metadata or {}).get("source") in {
            "windows_ui_automation", "windowhub_ui_automation"
        }
        and (e.metadata or {}).get("uia_visible") is True
        and (e.metadata or {}).get("uia_enabled") is True
        and not any("szablon" in p.casefold() or "wydruk" in p.casefold()
                    for p in panel_lineage(e))
    ][:limit]
    details = []
    if not observations:
        return {"status": "no_observed_dodaj", "selected_tab_status": tab_status, "buttons": []}
    hwnd = scene.observation.metadata.get("window_handle")
    if not isinstance(hwnd, int) or isinstance(hwnd, bool) or hwnd <= 0:
        return {"status": "missing_root_handle", "selected_tab_status": tab_status, "buttons": []}
    try:
        if desktop is None:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
        root = desktop.window(handle=hwnd).wrapper_object()
        all_wrappers = root.descendants()
    except Exception as exc:
        return {"status": "uia_probe_failed_" + type(exc).__name__,
                "selected_tab_status": tab_status, "buttons": []}

    # We compare runtime IDs from the scene, never only button text.
    from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider
    by_runtime = {}
    for wrapper in all_wrappers[:6000]:
        try:
            runtime_id = WindowHubUIAutomationProvider._runtime_id(wrapper)
            if runtime_id:
                by_runtime.setdefault(runtime_id, []).append(wrapper)
        except Exception:
            continue
    for element in observations:
        metadata = element.metadata or {}
        rid = metadata.get("uia_runtime_id")
        found = by_runtime.get(rid, []) if isinstance(rid, str) else []
        record = {
            "uia_match_count": len(found),
            "mdi_title_match_count": 0,
            "native_ancestor_windows": 0,
            "structural_chain": [],
        }
        if len(found) != 1:
            details.append(record)
            continue
        current = found[0]
        seen = set()
        for _ in range(16):
            try:
                current = current.parent()
                if current is None:
                    break
                info = current.element_info
                role = str(getattr(info, "control_type", "") or "").casefold()[:32]
                cls = str(getattr(info, "class_name", "") or "").casefold()[:64]
                handle = int(getattr(info, "handle", 0) or 0)
                if handle and handle not in seen:
                    seen.add(handle)
                    record["native_ancestor_windows"] += 1
                    title = str(getattr(info, "name", "") or "")
                    if native_title_matches(selected or "", title):
                        record["mdi_title_match_count"] += 1
                if len(record["structural_chain"]) < 10:
                    record["structural_chain"].append({
                        "role": role, "class": cls,
                        "has_hwnd": bool(handle),
                    })
            except Exception:
                break
        details.append(record)
    counts = Counter(rec["mdi_title_match_count"] for rec in details)
    return {
        "status": "diagnostic_only_no_native_authorization",
        "selected_tab_status": tab_status,
        "observed_dodaj": len(observations),
        "uia_matched_uniquely": sum(rec["uia_match_count"] == 1 for rec in details),
        "with_exact_mdi_ancestor": counts.get(1, 0),
        "with_no_mdi_ancestor": counts.get(0, 0),
        "with_ambiguous_mdi_ancestor": sum(v for k, v in counts.items() if k > 1),
        "buttons": details,
    }
