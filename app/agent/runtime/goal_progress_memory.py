"""Goal-agnostic short-term state tracker for the Windows UI agent.

This is NOT a scripted workflow and never chooses coordinates. It tracks
observable differences, prevents identical no-progress actions and tells
the reasoning model what changed. WindowHub is the first environment
adapter; the transition logic is generic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

_UIA = frozenset({"windowhub_ui_automation", "windows_ui_automation"})
_STATES = ("current_value", "uia_checked", "uia_selected")


def compact_state(scene: Any, *, stage: str | None = None) -> tuple:
    """Stable non-PII signature for an observation; no text values persisted."""
    state = scene.observation.state
    app = (getattr(state, "active_application", "") or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    window = stage or (getattr(state, "active_window_title", "") or "").strip().casefold()
    items = []
    for e in getattr(scene, "elements", ()) or ():
        m = e.metadata or {}
        if m.get("source") not in _UIA or m.get("uia_visible") is not True:
            continue
        # The element label may contain customer names; don't retain it.
        aid = m.get("automation_id")
        rid = m.get("uia_runtime_id")
        if not isinstance(aid, str) or not aid or not isinstance(rid, str) or not rid:
            continue
        signals = []
        for key in _STATES:
            value = m.get(key)
            if key == "current_value":
                # Hash only: changes detectable, user data not in diagnostics.
                v = sha256(value.encode("utf-8")).hexdigest()[:12] if isinstance(value, str) else None
            else:
                v = value if isinstance(value, bool) else None
            signals.append(v)
        items.append((e.kind, aid, tuple(signals)))
    return (app, window, tuple(sorted(set(items)))[:150]))


def action_identity(action: Any) -> tuple[str, str, str]:
    """Track action, semantic role and intended value without recording text."""
    target = getattr(action, "target", None)
    name = str(getattr(action, "name", "") or "")
    identity = (
        str(getattr(target, "automation_id", None) or "")
        + ":" + str(getattr(target, "role", None) or "")
    )
    value = getattr(action, "value", None)
    digest = sha256(str(value).encode("utf-8")).hexdigest()[:12] if value is not None else ""
    return name, identity, digest


@dataclass
class ProgressMemory:
    """Ephemeral per-goal execution memory, not permanent app training."""
    prior: tuple | None = None
    attempted: set[tuple] = field(default_factory=set)
    observations: int = 0
    changes: int = 0

    def observe(self, scene: Any, *, stage: str | None = None) -> dict:
        now = compact_state(scene, stage=stage)
        changed = self.prior is not None and now != self.prior
        if changed:
            self.changes += 1
        self.observations += 1
        self.prior = now
        return {
            "world_observation": self.observations,
            "world_changed_since_last": changed if self.observations > 1 else None,
            "world_observed_changes": self.changes,
            "stage": now[1],
            "visible_semantic_controls": len(now[2]),
        }

    def allow_action(self, action: Any, scene: Any, *, stage: str | None = None) -> tuple[bool, str]:
        sig = compact_state(scene, stage=stage)
        key = (sig, action_identity(action))
        if key in self.attempted:
            return False, "same_action_same_observation_no_new_evidence"
        self.attempted.add(key)
        return True, "new_observed_action"

    def feedback(self, scene: Any, *, stage: str | None = None) -> dict:
        current = compact_state(scene, stage=stage)
        changed = self.prior is not None and current != self.prior
        return {
            "source": "local_observation",
            "verified": False,  # Only actual executor/readback can verify.
            "stage": current[1],
            "observable_change": changed,
            "note": "No change is not automatically failure; outcome verification is separate.",
        }
