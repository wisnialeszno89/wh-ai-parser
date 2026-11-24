"""Virtual multi-document desktop with interruption-safe NaviMind mission sessions.

Pure Python and Codespaces-compatible. This is NOT real Windows automation,
does NOT switch users' windows, and never grants business persistence.
The mission stays pinned to one exact offer; other foreground offers pause it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.agent.runtime.navimind_mission_coordinator import (
    MissionAction, PositionTask, mission_progress_summary, next_mission_intent,
)
from app.agent.runtime.navimind_virtual_windowhub import VirtualWindowHub


class SessionStatus(str, Enum):
    ACTION = "action"
    PAUSED = "paused"
    COMPLETE = "complete"
    REVIEW = "review"


@dataclass(frozen=True)
class SessionEvent:
    status: SessionStatus
    action: str
    reason: str
    target_document: str
    foreground_document: str | None
    verified_position_count: int


@dataclass
class VirtualDesktopWorkspace:
    """Multiple isolated document stores with one foreground selection."""
    documents: dict[str, VirtualWindowHub]
    foreground_document: str | None = None

    def __post_init__(self):
        if len(set(self.documents)) != len(self.documents):
            raise ValueError("duplicate_documents")
        for doc_id, doc in self.documents.items():
            if doc_id != doc.document_id:
                raise ValueError("document_id_mismatch")
        if self.foreground_document is not None and self.foreground_document not in self.documents:
            raise ValueError("unknown_foreground_document")

    def foreground(self) -> VirtualWindowHub | None:
        if self.foreground_document is None:
            return None
        return self.documents.get(self.foreground_document)

    def select_document(self, document_id: str | None) -> None:
        if document_id is not None and document_id not in self.documents:
            raise ValueError("unknown_document")
        self.foreground_document = document_id


@dataclass
class PinnedMissionSession:
    """One supervised mission bound to a single offer's verified document id."""
    target_document: str
    tasks: tuple[PositionTask, ...]
    attempted_without_progress: set[str] = field(default_factory=set)
    history: list[SessionEvent] = field(default_factory=list)
    completed: bool = False
    last_seen_content: dict[str, tuple] = field(default_factory=dict)

    def __post_init__(self):
        if not self.target_document.strip():
            raise ValueError("target_document_required")
        if not self.tasks or len({t.position_id for t in self.tasks}) != len(self.tasks):
            raise ValueError("nonempty_unique_tasks_required")

    def _event(self, status: SessionStatus, action: str, reason: str,
               foreground: str | None, verified_count: int) -> SessionEvent:
        event = SessionEvent(status, action, reason, self.target_document,
                             foreground, verified_count)
        self.history.append(event)
        return event

    def step(self, workspace: VirtualDesktopWorkspace) -> SessionEvent:
        """Do at most one safe simulated action based on fresh observation.

        No UI action is performed if a different offer, other application or
        stale scene is active. A previously completed session still rechecks
        its postconditions before reporting completion.
        """
        env = workspace.foreground()
        if env is None or workspace.foreground_document != self.target_document:
            self.completed = False
            return self._event(
                SessionStatus.PAUSED, "none", "foreground_offer_changed",
                workspace.foreground_document, 0,
            )
        if (env.document_id != self.target_document
                or env.observed_application != "WindowHub" or env.stale):
            self.completed = False
            return self._event(
                SessionStatus.PAUSED, "none", "application_or_scene_not_verified",
                workspace.foreground_document, 0,
            )

        # Detect independent operator edits between steps. An old agent
        # target must not silently overwrite the salesperson's newer values.
        current_content = {
            position_id: (p.route, p.description, p.image_reference, p.unit_price)
            for position_id, p in env.positions.items()
            if position_id in {task.position_id for task in self.tasks}
        }
        changed = [
            key for key, observed in current_content.items()
            if key in self.last_seen_content
            and observed != self.last_seen_content[key]
        ]
        if changed:
            self.completed = False
            return self._event(
                SessionStatus.REVIEW, "none", "external_operator_edit_requires_review",
                workspace.foreground_document, 0,
            )
        self.last_seen_content = current_content
        readbacks = env.observe(self.tasks)
        scene = env.scene()
        summary = mission_progress_summary(self.tasks, scene, readbacks)
        verified_count = sum(
            bool(entry["quotation_position_complete"])
            for entry in summary["positions"]
        )
        # A human can change a price or remove an image after completion.
        # Never reuse old completion or previously observed editor state.
        intent = next_mission_intent(
            self.tasks, scene, readbacks,
            attempted_without_progress=tuple(self.attempted_without_progress),
        )
        if intent.action == MissionAction.COMPLETE:
            self.completed = bool(summary["all_position_requirements_verified"])
            return self._event(
                SessionStatus.COMPLETE if self.completed else SessionStatus.REVIEW,
                "complete", intent.reason, workspace.foreground_document,
                verified_count,
            )
        self.completed = False
        if intent.action == MissionAction.REVIEW:
            return self._event(
                SessionStatus.REVIEW, "none", intent.reason,
                workspace.foreground_document, verified_count,
            )
        if intent.action == MissionAction.OBSERVE:
            if (intent.reason == "activate_exact_position_before_editing"
                    and intent.position_id is not None
                    and env.activate(intent.position_id)):
                return self._event(
                    SessionStatus.ACTION, "activate_position",
                    "verified_existing_position_activated",
                    workspace.foreground_document, verified_count,
                )
            return self._event(
                SessionStatus.PAUSED, "none", intent.reason,
                workspace.foreground_document, verified_count,
            )

        # Even in simulation the intent is never a native action. This
        # adapter checks the exact document and current position first.
        action_id = str(intent.position_id) + ":" + intent.action.value
        accepted = env.apply(intent, self.tasks)
        if not accepted:
            self.attempted_without_progress.add(action_id)
            return self._event(
                SessionStatus.REVIEW, intent.action.value,
                "action_not_verified_no_blind_retry",
                workspace.foreground_document, verified_count,
            )
        # Track our own dispatched change so it is not mistaken for a later
        # independent operator edit. Readback still occurs on the next cycle.
        self.last_seen_content = {
            position_id: (p.route, p.description, p.image_reference, p.unit_price)
            for position_id, p in env.positions.items()
            if position_id in {task.position_id for task in self.tasks}
        }
        # A command accepted by the simulator is not the business postcondition.
        # Re-observe on the next step to independently determine progress.
        return self._event(
            SessionStatus.ACTION, intent.action.value,
            "simulated_dispatch_reobserve_next_step",
            workspace.foreground_document, verified_count,
        )

    def report(self, workspace: VirtualDesktopWorkspace) -> dict:
        """Read-only progress report, no success claim for wrong foreground."""
        env = workspace.documents.get(self.target_document)
        if env is None:
            return {
                "target_document": self.target_document, "status": "unknown_target",
                "verified": False, "agent_authorized_to_save": False,
                "agent_authorized_to_send": False,
            }
        result = mission_progress_summary(self.tasks, env.scene(), env.observe(self.tasks))
        return {
            **result,
            "target_document": self.target_document,
            "foreground_document": workspace.foreground_document,
            "status": (
                "current_target" if workspace.foreground_document == self.target_document
                and not env.stale and env.observed_application == "WindowHub"
                else "paused_not_current"
            ),
            "verified": (
                workspace.foreground_document == self.target_document
                and not env.stale
                and env.observed_application == "WindowHub"
                and result["all_position_requirements_verified"]
            ),
        }
