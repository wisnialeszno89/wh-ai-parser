"""Fail-closed V2 scene freshness guard for model latency and human takeover.

The model's old reference map remains valid only when a newly observed desktop
matches the exact protected scene snapshot. The hash is ephemeral, never
logged, and does not prove safety against same-state ABA or simultaneous input:
a future native input arbiter must enforce ownership at dispatch.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from app.agent.runtime.goal_progress_memory import compact_state


@dataclass(frozen=True)
class SceneGuardResult:
    safe: bool
    reason: str


def _digest(value: Any) -> str:
    return sha256(repr(value).encode("utf-8")).hexdigest()


def _stage(scene: Any) -> str:
    from app.agent.learning.windowhub_demonstration import stage_of
    return stage_of(scene) or "unknown"


def _identity(scene: Any) -> tuple:
    observation = scene.observation
    state = observation.state
    metadata = observation.metadata or {}
    application = (getattr(state, "active_application", "") or "").replace(
        "\\", "/"
    ).rsplit("/", 1)[-1].casefold()
    title = (getattr(state, "active_window_title", "") or "").strip()
    hwnd = metadata.get("window_handle")
    # A title alone is not a complete MDI identity, but any title or
    # foreground HWND change is a hard stop.
    selected = []
    for element in getattr(scene, "elements", ()) or ():
        m = element.metadata or {}
        if (element.kind == "tabitem"
                and m.get("uia_tab_scope") == "document"
                and m.get("uia_selected") is True
                and m.get("uia_visible") is True):
            selected.append((
                _digest((element.label or "").strip()),
                m.get("uia_runtime_id"),
            ))
    return application, _digest(title), hwnd, tuple(sorted(selected, key=repr))


def _control_context(scene: Any) -> tuple:
    """Hash sensitive labels/values but track focus, enabled and scope changes."""
    tracked = []
    for element in getattr(scene, "elements", ()) or ():
        m = element.metadata or {}
        if m.get("source") not in ("windows_ui_automation", "windowhub_ui_automation"):
            continue
        if m.get("uia_visible") is not True:
            continue
        value = m.get("current_value")
        tracked.append((
            element.kind,
            m.get("automation_id"),
            m.get("uia_runtime_id"),
            _digest(element.label) if isinstance(element.label, str) else None,
            _digest(value) if isinstance(value, str) else None,
            m.get("uia_checked"),
            m.get("uia_selected"),
            m.get("uia_focused"),
            m.get("uia_enabled"),
            _digest(m.get("document_scope")) if m.get("document_scope") is not None else None,
        ))
    return tuple(sorted(tracked, key=repr))


def _signature(scene: Any) -> tuple:
    # Include stable progress signature plus newly tracked focus/enabled/owner.
    # No raw customer names or field values leave this function.
    return compact_state(scene), _control_context(scene)


def compare_preaction_scenes(before: Any, after: Any) -> SceneGuardResult:
    """Require a fresh locally observed scene identical to model-time scene.

    Pure comparisons only. No UI actions, network requests or persistence.
    Any missing observation or ambiguous document selection is rejected.
    """
    if before is None or after is None:
        return SceneGuardResult(False, "preaction_observation_missing")
    try:
        old_identity = _identity(before)
        new_identity = _identity(after)
        old_stage = _stage(before)
        new_stage = _stage(after)
        if old_identity[0] != "okna.exe" or new_identity[0] != "okna.exe":
            return SceneGuardResult(False, "preaction_windowhub_not_foreground")
        if old_identity != new_identity:
            return SceneGuardResult(False, "preaction_foreground_or_document_changed")
        if old_stage != new_stage or old_stage == "unknown":
            return SceneGuardResult(False, "preaction_workflow_stage_changed_or_unknown")
        if _signature(before) != _signature(after):
            return SceneGuardResult(False, "preaction_uia_state_changed")
        # If the UI says an offer document is active, demand exactly one
        # selected document tab. Otherwise a same-caption sibling MDI item
        # could be mistaken for the originally selected offer.
        if old_stage == "offer_document" and len(new_identity[3]) != 1:
            return SceneGuardResult(False, "preaction_selected_offer_unverified")
        return SceneGuardResult(True, "preaction_scene_unchanged")
    except (AttributeError, TypeError, ValueError, KeyError):
        return SceneGuardResult(False, "preaction_scene_unreadable")


def verify_preaction_scene(loop: Any, model_scene: Any) -> tuple[SceneGuardResult, Any]:
    """Re-observe immediately before V2 action dispatch; fail closed."""
    try:
        fresh = loop.observe_scene()
    except Exception:
        return SceneGuardResult(False, "preaction_reobservation_failed"), None
    return compare_preaction_scenes(model_scene, fresh), fresh
