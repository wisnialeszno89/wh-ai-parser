"""Explicit human/agent turn-taking for the portable NaviMind session.

Offline policy only. No device monitoring, background polling, timers,
Windows hooks or automatic keyboard/mouse operations are implemented here.
The host integrates pause/release events and invokes tick() at safe boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.agent.runtime.navimind_virtual_desktop_workspace import (
    PinnedMissionSession, SessionEvent, SessionStatus, VirtualDesktopWorkspace,
)


class ControlOwner(str, Enum):
    AGENT = "agent"
    HUMAN = "human"


class HandoffStatus(str, Enum):
    PAUSED_BY_HUMAN = "paused_by_human"
    RESUME_READY = "resume_ready"
    RESUME_BLOCKED = "resume_blocked"
    AGENT_ACTION = "agent_action"
    AGENT_COMPLETE = "agent_complete"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class HandoffEvent:
    status: HandoffStatus
    owner: ControlOwner
    reason: str
    epoch: int
    action: str = "none"
    document_id: str | None = None


@dataclass
class HumanHandoffController:
    """Human wins every control conflict; no stale executor permission.

    An explicit human takeover increments the control epoch so a queued model
    action produced before the handoff is invalid. On release, the next tick
    reobserves exact document, active position, and application state.
    Operator edits must be reviewed instead of being silently overwritten.
    """
    session: PinnedMissionSession
    owner: ControlOwner = ControlOwner.AGENT
    epoch: int = 0
    history: list[HandoffEvent] = field(default_factory=list)
    pending_review: bool = False

    def _record(self, status: HandoffStatus, reason: str, action: str = "none") -> HandoffEvent:
        event = HandoffEvent(
            status=status, owner=self.owner, reason=reason,
            epoch=self.epoch, action=action, document_id=self.session.target_document,
        )
        self.history.append(event)
        return event

    def take_over(self) -> HandoffEvent:
        """User takes control; the current and all older plans are invalid."""
        self.epoch += 1
        self.owner = ControlOwner.HUMAN
        return self._record(HandoffStatus.PAUSED_BY_HUMAN, "explicit_user_takeover")

    def release(self) -> HandoffEvent:
        """Return control; actual continuation is a separate fresh tick."""
        if self.owner == ControlOwner.HUMAN:
            self.epoch += 1
            self.owner = ControlOwner.AGENT
        return self._record(
            HandoffStatus.RESUME_READY, "fresh_reobservation_required_before_next_action"
        )

    def is_action_epoch_current(self, epoch: int) -> bool:
        """Executor must check this immediately before applying an action."""
        return self.owner == ControlOwner.AGENT and type(epoch) is int and epoch == self.epoch

    def tick(self, workspace: VirtualDesktopWorkspace, *,
             prepared_epoch: int | None = None) -> HandoffEvent:
        """Execute at most one virtual step after checking current ownership.

        A stale asynchronous model proposal never survives a human handoff,
        even when the user has already released control.
        """
        if self.owner == ControlOwner.HUMAN:
            return self._record(HandoffStatus.PAUSED_BY_HUMAN, "user_currently_controls_desktop")
        if prepared_epoch is not None and not self.is_action_epoch_current(prepared_epoch):
            return self._record(HandoffStatus.RESUME_BLOCKED, "stale_plan_epoch_reobserve")
        if self.pending_review:
            return self._record(HandoffStatus.NEEDS_REVIEW, "human_changes_pending_review")

        result: SessionEvent = self.session.step(workspace)
        if result.status == SessionStatus.ACTION:
            return self._record(HandoffStatus.AGENT_ACTION, result.reason, result.action)
        if result.status == SessionStatus.COMPLETE:
            return self._record(HandoffStatus.AGENT_COMPLETE, result.reason, result.action)
        if result.status == SessionStatus.REVIEW:
            self.pending_review = True
            return self._record(HandoffStatus.NEEDS_REVIEW, result.reason)
        return self._record(HandoffStatus.RESUME_BLOCKED, result.reason)

    def clear_review_after_operator_replan(self) -> None:
        """An explicit approved replan may unlock execution.

        This does NOT update mission specifications, accept conflicting data,
        clear no-progress action history, or authorize a save. Callers must
        adjust approved requirements separately; otherwise reobservation
        will rediscover the same conflict and block again.
        """
        self.pending_review = False
