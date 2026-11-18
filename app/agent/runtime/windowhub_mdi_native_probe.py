"""Read-only MDI ancestry probe for WindowHub's duplicate toolbar buttons.

The ordinary UIA document_scope is often None because an MDI content panel
is NOT inside its document TabItem. Diagnose the native Win32 child-window
chain instead. Never click and never infer ownership from button order.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
import re

# Observed WH captions include OFR/4687- and OFR/4488-4300 <>.
# A parsed number is not proof of ownership; native MDI hierarchy and exact
# selected-tab caption must still agree before enabling any action.
_OFFER_CAPTION = re.compile(r"^OFR/\d+(?:-\d+)*-?(?:\s*<>)?$", re.IGNORECASE)
_ORDER_CAPTION = re.compile(r"^ZLC/\d+(?:-\d+)*-?(?:\s+.{1,160})?$", re.IGNORECASE)


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
    scope_status = []
    unknown = 0
    for titles in candidate_ancestor_titles:
        matching = sum(native_title_matches(selected_document or "", title) for title in titles)
        matched.append(matching)
        distinct_doc_names = {
            title.strip().casefold() for title in titles
            if isinstance(title, str)
            and _OFFER_CAPTION.fullmatch(title.strip())
        }
        if matching == 1 and len(distinct_doc_names) == 1:
            scope_status.append("matching_mdi_ancestor")
        elif matching == 0 and len(distinct_doc_names) == 1:
            scope_status.append("other_mdi_ancestor")
        else:
            scope_status.append("unresolved")
            unknown += 1
    safe = (
        bool(selected_document)
        and unknown == 0
        and scope_status.count("matching_mdi_ancestor") == 1
    )
    return MdiProbe(
        observed_buttons=len(candidate_ancestor_titles),
        selected_document_verified=bool(selected_document),
        scope_candidates=tuple(scope_status),
        native_caption_matches=tuple(matched),
        native_distinct_roots=0,
        unknown_buttons=unknown,
        status="candidate_for_structural_validation" if safe else "native_mdi_scope_unresolved",
    )


def _mdi_document_classification(wrapper, selected: str | None) -> str:
    """Describe the nearest proven MDI child without revealing document data.

    Diagnostic ONLY; even a matching category does not authorize a click.
    """
    current = wrapper
    for _ in range(16):
        try:
            parent = current.parent()
            if parent is None:
                break
            info = parent.element_info
            if (
                str(getattr(info, "control_type", "") or "").casefold() == "window"
                and int(getattr(info, "handle", 0) or 0) > 0
            ):
                host = parent.parent()
                if host is not None:
                    host_info = host.element_info
                    if (
                        str(getattr(host_info, "class_name", "") or "").casefold() == "mdiclient"
                        and int(getattr(host_info, "handle", 0) or 0) > 0
                    ):
                        title = str(getattr(info, "name", "") or "").strip()
                        if _OFFER_CAPTION.fullmatch(title):
                            return "active_offer" if native_title_matches(selected or "", title) else "other_offer"
                        if title.casefold().startswith("zlc/"):
                            return "order_read_only"
                        return "unrecognized_mdi_child"
            current = parent
        except (AttributeError, ValueError, TypeError, OSError):
            break
    return "no_proven_mdi_child"


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
            "mdi_child_classification": "uia_unresolved",
            "structural_chain": [],
        }
        if len(found) != 1:
            details.append(record)
            continue
        record["mdi_child_classification"] = _mdi_document_classification(found[0], selected)
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


def _document_from_native_chain(wrapper) -> str | None:
    """Recognize WindowHub document child Window -> MDIClient structure."""
    current = wrapper
    for _ in range(16):
        try:
            parent = current.parent()
            if parent is None:
                return None
            info = parent.element_info
            role = str(getattr(info, "control_type", "") or "").casefold()
            title = str(getattr(info, "name", "") or "").strip()
            native = int(getattr(info, "handle", 0) or 0)
            if (role == "window" and native > 0
                    and _OFFER_CAPTION.fullmatch(title)):
                host = parent.parent()
                host_info = host.element_info
                if (str(getattr(host_info, "class_name", "") or "").casefold()
                        == "mdiclient"
                        and int(getattr(host_info, "handle", 0) or 0) > 0):
                    return title
            current = parent
        except (AttributeError, ValueError, TypeError, OSError):
            return None
    return None


def _scoped_owner_from_native_chain(wrapper) -> str | None:
    """Prove an offer OR order owner through a native MDI child window.

    This returns a document caption for structural scoping only. It never
    grants edit permission, especially to any ZLC document.
    """
    current = wrapper
    for _ in range(16):
        try:
            parent = current.parent()
            if parent is None:
                return None
            info = parent.element_info
            role = str(getattr(info, "control_type", "") or "").casefold()
            title = str(getattr(info, "name", "") or "").strip()
            native = int(getattr(info, "handle", 0) or 0)
            if role == "window" and native > 0:
                host = parent.parent()
                if host is not None:
                    host_info = host.element_info
                    if (
                        str(getattr(host_info, "class_name", "") or "").casefold() == "mdiclient"
                        and int(getattr(host_info, "handle", 0) or 0) > 0
                    ):
                        if _OFFER_CAPTION.fullmatch(title) or _ORDER_CAPTION.fullmatch(title):
                            return title
                        # An unidentified MDI child is not a known owner.
                        return None
            current = parent
        except (AttributeError, ValueError, TypeError, OSError):
            return None
    return None


def _provably_outside_mdi_client(wrapper) -> bool:
    """Prove the wrapper is outside every MDIClient, not just lacking a caption.

    A truncated, failing, cyclic or ambiguous ancestry chain is never proof.
    """
    current = wrapper
    # Hold strong references: pywinauto can create new wrapper objects for
    # every .parent() call. Using id() without retaining them may falsely
    # report a cycle when CPython reuses a released object address.
    seen = {}
    for _ in range(40):
        try:
            parent = current.parent()
            if parent is None:
                return True
            if id(parent) in seen:
                return False
            seen[id(parent)] = parent
            info = parent.element_info
            if str(getattr(info, "class_name", "") or "").casefold() == "mdiclient":
                return False
            current = parent
        except (AttributeError, ValueError, TypeError, OSError):
            return False
    return False


def unknown_mdi_ancestry_reason(wrapper) -> str:
    """Classify missing owner without exposing titles, HWNDs or private text."""
    current = wrapper
    # Hold strong references: pywinauto can create new wrapper objects for
    # every .parent() call. Using id() without retaining them may falsely
    # report a cycle when CPython reuses a released object address.
    seen = {}
    for _ in range(40):
        try:
            parent = current.parent()
            if parent is None:
                return "chain_ended_without_proven_owner"
            signature = id(parent)
            if signature in seen:
                return "cyclic_parent_chain"
            seen[signature] = parent
            info = parent.element_info
            class_name = str(getattr(info, "class_name", "") or "").casefold()
            role = str(getattr(info, "control_type", "") or "").casefold()
            if class_name == "mdiclient":
                return "mdi_client_without_recognized_child"
            if role == "window" and not int(getattr(info, "handle", 0) or 0):
                return "window_ancestor_without_native_handle"
            current = parent
        except (AttributeError, ValueError, TypeError, OSError):
            return "parent_chain_unavailable"
    return "parent_chain_depth_exceeded"


def unresolved_mdi_child_shape(wrapper, *, selected: str | None = None) -> dict:
    """Read-only, privacy-safe type of the immediate child of MDIClient.

    No captions, HWNDs, runtime IDs or screen coordinates leave this function.
    The result is diagnostic, never authority to select a button.
    """
    current = wrapper
    keep_alive = {}
    for depth in range(40):
        try:
            parent = current.parent()
            if parent is None:
                return {"kind": "mdi_parent_not_found"}
            if id(parent) in keep_alive:
                return {"kind": "cyclic_ancestry"}
            keep_alive[id(parent)] = parent
            parent_info = parent.element_info
            parent_class = str(getattr(parent_info, "class_name", "") or "").casefold()
            if parent_class == "mdiclient":
                info = current.element_info
                role = str(getattr(info, "control_type", "") or "").casefold()
                cls = str(getattr(info, "class_name", "") or "").casefold()
                handle_present = int(getattr(info, "handle", 0) or 0) > 0
                title = str(getattr(info, "name", "") or "").strip()
                if not title:
                    caption_kind = "empty"
                elif _OFFER_CAPTION.fullmatch(title):
                    caption_kind = "offer_same" if native_title_matches(
                        selected or "", title
                    ) else "offer_other"
                elif _ORDER_CAPTION.fullmatch(title):
                    caption_kind = "order"
                else:
                    caption_kind = "other_or_nonstandard"
                return {
                    "kind": "mdi_immediate_child",
                    "depth": depth,
                    "role": role[:32],
                    "class": cls[:64],
                    "native_handle_present": handle_present,
                    "caption_kind": caption_kind,
                }
            current = parent
        except (AttributeError, ValueError, TypeError, OSError):
            return {"kind": "ancestry_unavailable"}
    return {"kind": "ancestry_depth_exceeded"}


_INACTIVE_MDI_SCOPE = "__inactive_mdi_sibling__"


class _Win32Mdi:
    """Read-only HWND queries. WM_MDIGETACTIVE is bounded for a hung UI."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        api = ctypes.WinDLL("user32", use_last_error=True)
        self.parent = api.GetAncestor
        self.parent.argtypes = [wintypes.HWND, wintypes.UINT]
        self.parent.restype = wintypes.HWND
        self.foreground = api.GetForegroundWindow
        self.foreground.argtypes = []
        self.foreground.restype = wintypes.HWND
        self._class_name = api.GetClassNameW
        self._class_name.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self._class_name.restype = ctypes.c_int
        self._title = api.GetWindowTextW
        self._title.argtypes = self._class_name.argtypes
        self._title.restype = ctypes.c_int
        self._send = api.SendMessageTimeoutW
        self._send.argtypes = [
            wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t,
            wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t),
        ]
        self._send.restype = ctypes.c_ssize_t

    def active_child(self, host):
        import ctypes

        value = ctypes.c_size_t()
        # WM_MDIGETACTIVE, no output pointer in lParam; SMTO_ABORTIFHUNG.
        if self._send(host, 0x0229, 0, 0, 0x0002, 250, ctypes.byref(value)):
            return value.value
        return 0

    def class_name(self, hwnd):
        import ctypes

        buffer = ctypes.create_unicode_buffer(256)
        self._class_name(hwnd, buffer, len(buffer))
        return buffer.value

    def title(self, hwnd):
        import ctypes

        buffer = ctypes.create_unicode_buffer(256)
        self._title(hwnd, buffer, len(buffer))
        return buffer.value


def _win32_mdi_lineage(wrapper, api) -> tuple[int, int] | None:
    """Return (MDIClient, direct child) only when UIA and Win32 paths agree."""
    current = wrapper
    native_anchor = 0
    for _ in range(16):
        info = current.element_info
        handle = int(getattr(info, "handle", 0) or 0)
        native_anchor = native_anchor or handle
        parent = current.parent()
        if parent is None:
            return None
        host_info = parent.element_info
        if str(getattr(host_info, "class_name", "") or "").casefold() == "mdiclient":
            host = int(getattr(host_info, "handle", 0) or 0)
            if not host or not handle or api.class_name(host).casefold() != "mdiclient":
                return None
            if api.parent(handle, 1) != host:  # GA_PARENT, never the popup owner.
                return None
            for _ in range(16):
                if native_anchor == handle:
                    return host, handle
                if not native_anchor or native_anchor == host:
                    break
                native_anchor = api.parent(native_anchor, 1)
            return None
        current = parent
    return None


def _verified_inactive_mdi_siblings(wrappers, selected, root, api) -> tuple[set[int], str]:
    """Exclude unknown controls only by positive, same-host sibling evidence."""
    if api.foreground() != root:
        return set(), "foreground_changed"
    active_candidates = [
        w for w in wrappers
        if native_title_matches(selected, _scoped_owner_from_native_chain(w) or "")
    ]
    if len(active_candidates) != 1:
        return set(), "titled_active_candidate_not_unique"
    lineage = _win32_mdi_lineage(active_candidates[0], api)
    if lineage is None:
        return set(), "active_candidate_lineage_unverified"
    host, child = lineage
    if api.parent(host, 2) != root:  # GA_ROOT follows parent links.
        return set(), "host_outside_foreground"
    if api.active_child(host) != child or not native_title_matches(selected, api.title(child)):
        return set(), "active_mdi_disagrees"
    excluded = set()
    for wrapper in wrappers:
        if _scoped_owner_from_native_chain(wrapper) is not None:
            continue
        sibling = _win32_mdi_lineage(wrapper, api)
        if sibling is not None and sibling[0] == host and sibling[1] != child:
            excluded.add(id(wrapper))
    if (api.foreground() != root or api.active_child(host) != child
            or not native_title_matches(selected, api.title(child))):
        return set(), "active_mdi_changed"
    return excluded, "inactive_sibling_verified" if excluded else "no_inactive_sibling_proven"


def verify_mdi_add_hit(point, *, root, expected_offer, metadata, desktop=None, win32=None) -> bool:
    """Rebind the mouse point to the exact live UIA control in the active child."""
    try:
        from app.agent.perception.windowhub_ui_automation_provider import (
            WindowHubUIAutomationProvider,
        )

        api = win32 if win32 is not None else _Win32Mdi()
        if api.foreground() != root:
            return False
        if desktop is None:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
        hit = desktop.from_point(*point)
        info = hit.element_info
        if (
            str(info.name or "").strip().casefold() != "dodaj"
            or str(info.control_type or "").casefold() != "button"
            or not info.visible or not info.enabled
            or info.automation_id != metadata.get("automation_id")
            or WindowHubUIAutomationProvider._runtime_id(hit) != metadata.get("uia_runtime_id")
            or not native_title_matches(expected_offer, _scoped_owner_from_native_chain(hit) or "")
        ):
            return False
        lineage = _win32_mdi_lineage(hit, api)
        if lineage is None:
            return False
        host, child = lineage
        return (
            api.parent(host, 2) == root
            and api.active_child(host) == child
            and native_title_matches(expected_offer, api.title(child))
            and native_title_matches("Okna - " + expected_offer, api.title(root))
            and api.foreground() == root
        )
    except Exception:
        return False


def _inactive_mdi_evidence(wrappers, selected, root, *, win32):
    if not any(
        _scoped_owner_from_native_chain(w) is None and not _provably_outside_mdi_client(w)
        for w in wrappers
    ):
        return set(), "not_needed"
    try:
        api = win32 if win32 is not None else _Win32Mdi()
        return _verified_inactive_mdi_siblings(wrappers, selected, root, api)
    except Exception as exc:
        return set(), "win32_query_failed_" + type(exc).__name__


def diagnose_native_scope_enrichment(scene, *, desktop=None, win32=None) -> dict:
    """Explain precisely why scope enrichment stopped, without UI values/IDs.

    This is diagnostic evidence only and does not authorize any input.
    """
    from app.agent.runtime.active_document_scope import selected_document_tab
    from app.agent.runtime.active_panel_context import panel_lineage
    import os

    result = {
        "status": "not_started",
        "active_title_matches_selected_tab": False,
        "controls": 0,
        "runtime_unique": 0,
        "native_owner_active": 0,
        "native_owner_other": 0,
        "proven_outside_mdi": 0,
        "proven_inactive_mdi_siblings": 0,
        "win32_mdi_status": "not_started",
        "unresolved_ancestry": 0,
        "unresolved_reasons": {},
        "unresolved_mdi_child_shapes": [],
        "existing_scope_conflicts": 0,
    }
    title = (scene.observation.state.active_window_title or "").strip()
    app = (scene.observation.state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    if app != "okna.exe" or not title.casefold().startswith("okna - ofr/"):
        result["status"] = "not_offer_foreground"
        return result
    selected, reason = selected_document_tab(scene)
    result["selected_tab_status"] = reason
    if not selected:
        result["status"] = "selected_tab_missing"
        return result
    result["active_title_matches_selected_tab"] = native_title_matches(
        selected, title[len("Okna - "):]
    )
    if not result["active_title_matches_selected_tab"]:
        result["status"] = "selected_tab_and_foreground_disagree"
        return result
    if os.name != "nt" and desktop is None:
        result["status"] = "windows_required"
        return result

    controls = [
        e for e in scene.elements
        if e.kind == "button"
        and (e.label or "").strip().casefold() == "dodaj"
        and (e.metadata or {}).get("source") in {
            "windows_ui_automation", "windowhub_ui_automation"
        }
        and (e.metadata or {}).get("uia_visible") is True
        and (e.metadata or {}).get("uia_enabled") is True
        and not any(
            "szablon" in p.casefold() or "wydruk" in p.casefold()
            for p in panel_lineage(e)
        )
    ]
    result["controls"] = len(controls)
    if not 1 <= len(controls) <= 8:
        result["status"] = "control_count_outside_limit"
        return result
    hwnd = scene.observation.metadata.get("window_handle")
    if isinstance(hwnd, bool) or not isinstance(hwnd, int) or hwnd <= 0:
        result["status"] = "missing_native_root_handle"
        return result
    try:
        if desktop is None:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
        from app.agent.perception.windowhub_ui_automation_provider import (
            WindowHubUIAutomationProvider,
        )
        descendants = desktop.window(handle=hwnd).wrapper_object().descendants()
        mapping = {}
        for wrapper in descendants[:6000]:
            rid = WindowHubUIAutomationProvider._runtime_id(wrapper)
            if isinstance(rid, str) and rid:
                mapping.setdefault(rid, []).append(wrapper)
        matched = [mapping.get((e.metadata or {}).get("uia_runtime_id"), []) for e in controls]
        if all(len(wrappers) == 1 for wrappers in matched):
            excluded, result["win32_mdi_status"] = _inactive_mdi_evidence(
                [wrappers[0] for wrappers in matched], selected, hwnd, win32=win32,
            )
        else:
            excluded = set()
            result["win32_mdi_status"] = "runtime_identity_unverified"
        for element in controls:
            rid = (element.metadata or {}).get("uia_runtime_id")
            found = mapping.get(rid, [])
            if len(found) != 1:
                result["unresolved_ancestry"] += 1
                continue
            result["runtime_unique"] += 1
            owner = _scoped_owner_from_native_chain(found[0])
            if owner:
                if native_title_matches(selected, owner):
                    result["native_owner_active"] += 1
                else:
                    result["native_owner_other"] += 1
            elif id(found[0]) in excluded:
                result["proven_inactive_mdi_siblings"] += 1
                owner = _INACTIVE_MDI_SCOPE
            elif _provably_outside_mdi_client(found[0]):
                result["proven_outside_mdi"] += 1
                owner = "__outside_mdi__"
            else:
                result["unresolved_ancestry"] += 1
                reason = unknown_mdi_ancestry_reason(found[0])
                reasons = result["unresolved_reasons"]
                reasons[reason] = reasons.get(reason, 0) + 1
                if reason == "mdi_client_without_recognized_child":
                    result["unresolved_mdi_child_shapes"].append(
                        unresolved_mdi_child_shape(found[0], selected=selected)
                    )
            existing = (element.metadata or {}).get("document_scope")
            if existing is not None and existing != owner:
                # This remains only an indicator; never fixes source metadata.
                result["existing_scope_conflicts"] += 1
        if result["unresolved_ancestry"]:
            result["status"] = "unresolved_native_ancestry"
        elif result["native_owner_active"] != 1:
            result["status"] = "active_owner_not_unique"
        elif result["existing_scope_conflicts"]:
            result["status"] = "existing_scope_conflict"
        else:
            result["status"] = "scope_evidence_candidate"
    except Exception as exc:
        result["status"] = "native_probe_error_" + type(exc).__name__
    return result


def enrich_native_mdi_document_scope(scene, *, desktop=None, win32=None):
    """Attach verified OFR/ZLC owners; classify unrelated global controls structurally.

    Read-only. Unknown/duplicate/cross-document evidence never authorizes
    a candidate. Re-run on every observation rather than caching a position.
    """
    from dataclasses import replace
    from app.agent.runtime.active_document_scope import selected_document_tab
    from app.agent.runtime.active_panel_context import panel_lineage
    import os

    title = (scene.observation.state.active_window_title or "").strip()
    app = (scene.observation.state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    if app != "okna.exe" or not title.casefold().startswith("okna - ofr/"):
        return scene
    selected, _ = selected_document_tab(scene)
    if not selected or not native_title_matches(selected, title[len("Okna - "):]):
        return scene
    if os.name != "nt" and desktop is None:
        return scene
    controls = [
        e for e in scene.elements
        if e.kind == "button"
        and (e.label or "").strip().casefold() == "dodaj"
        and (e.metadata or {}).get("source") in {
            "windows_ui_automation", "windowhub_ui_automation"
        }
        and (e.metadata or {}).get("uia_visible") is True
        and (e.metadata or {}).get("uia_enabled") is True
        and not any("szablon" in name.casefold() or "wydruk" in name.casefold()
                    for name in panel_lineage(e))
    ]
    if not controls or len(controls) > 8:
        return scene
    hwnd = scene.observation.metadata.get("window_handle")
    if isinstance(hwnd, bool) or not isinstance(hwnd, int) or hwnd <= 0:
        return scene
    try:
        if desktop is None:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
        from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider
        descendants = desktop.window(handle=hwnd).wrapper_object().descendants()
        mapping = {}
        for control in descendants[:6000]:
            rid = WindowHubUIAutomationProvider._runtime_id(control)
            if isinstance(rid, str) and rid:
                mapping.setdefault(rid, []).append(control)
        matched = [mapping.get((e.metadata or {}).get("uia_runtime_id"), []) for e in controls]
        if any(len(wrappers) != 1 for wrappers in matched):
            return scene
        wrappers = [match[0] for match in matched]
        if len({id(wrapper) for wrapper in wrappers}) != len(wrappers):
            return scene
        excluded, _ = _inactive_mdi_evidence(wrappers, selected, hwnd, win32=win32)
        scoped = {}
        for element, wrapper in zip(controls, wrappers):
            owner = _scoped_owner_from_native_chain(wrapper)
            if owner:
                scoped[id(element)] = (owner, "verified_native_mdi_child")
            elif id(wrapper) in excluded:
                scoped[id(element)] = (_INACTIVE_MDI_SCOPE, "verified_inactive_mdi_sibling")
            elif _provably_outside_mdi_client(wrapper):
                scoped[id(element)] = ("__outside_mdi__", "verified_outside_mdi")
            else:
                # Never reuse a prior association when fresh proof is missing.
                return scene
        if sum(native_title_matches(selected, owner) for owner, _ in scoped.values()) != 1:
            return scene
        if any(
            (e.metadata or {}).get("document_scope") not in (None, scoped[id(e)][0])
            for e in controls if id(e) in scoped
        ):
            return scene
        return replace(
            scene,
            elements=tuple(
                replace(e, metadata={
                    **(e.metadata or {}),
                    "document_scope": scoped[id(e)][0],
                    "document_scope_source": scoped[id(e)][1],
                }) if id(e) in scoped else e
                for e in scene.elements
            ),
        )
    except Exception:
        return scene
