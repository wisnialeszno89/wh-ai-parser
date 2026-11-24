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


def _signature(scene: Any) -> tuple:
    # compact_state includes a hashed UIA field value, checked/selected state,
    # and identities of visible controls, without retaining raw customer data.
    # Explicit stage does NOT replace window title for this signature.
    return _identity(scene), _stage(scene), compact_state(scene)


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
        if compact_state(before) != compact_state(after):
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
