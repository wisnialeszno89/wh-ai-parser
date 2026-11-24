"""Local, thread-safe input ownership and stale-plan invalidation.

This is a policy gate for a native desktop input dispatcher, not an OS-wide
mouse/keyboard hook. A host must route ALL agent input through dispatch()
and expose takeover/release controls to the operator. Human takeover signals
intent immediately and waits for any already-running atomic action to finish.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from secrets import token_urlsafe
from threading import Event, RLock
from typing import Callable, TypeVar

T = TypeVar("T")


class InputOwner(str, Enum):
    AGENT = "agent"
    HUMAN = "human"


class InputDenied(RuntimeError):
    """Stable denial code; never contains customer data."""


@dataclass(frozen=True)
class ActionPermit:
    epoch: int
    document_key: str
    nonce: str = ""
    # Permit represents a planning snapshot, NOT persistent GUI authority.


class LocalInputArbiter:
    """Cooperative single-process arbiter for agent desktop operations.

    Only the host can call agent dispatch. The human can request takeover
    even during model reasoning: that immediately sets the takeover signal.
    All queued permits are invalidated by the next epoch; none can be reused.
    During a native operation, takeover waits for the atomic dispatch to end
    rather than interrupting a half-complete keyboard or mouse operation.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._takeover_requested = Event()
        self._owner = InputOwner.AGENT
        self._epoch = 0
        self._document_key: str | None = None
        self._permit_nonce: str | None = None
        self._reobservation_required = True

    def takeover(self) -> int:
        """Signal immediately; then acquire control after any atomic action."""
        self._takeover_requested.set()
        with self._lock:
            self._epoch += 1
            self._owner = InputOwner.HUMAN
            self._document_key = None
            self._permit_nonce = None
            self._reobservation_required = True
            return self._epoch

    def release(self) -> int:
        """Release human control; fresh observation is still mandatory."""
        with self._lock:
            if self._owner != InputOwner.HUMAN:
                raise InputDenied("release_requires_human_ownership")
            self._epoch += 1
            self._owner = InputOwner.AGENT
            self._document_key = None
            self._reobservation_required = True
            self._takeover_requested.clear()
            return self._epoch

    def observe_document(self, document_key: str) -> ActionPermit:
        """Confirm exact observed document AFTER takeover or scene change."""
        if not isinstance(document_key, str) or not document_key.strip():
            raise InputDenied("verified_document_key_required")
        with self._lock:
            if self._takeover_requested.is_set() or self._owner != InputOwner.AGENT:
                raise InputDenied("human_controls_desktop")
            self._document_key = document_key
            self._permit_nonce = token_urlsafe(24)
            self._reobservation_required = False
            return ActionPermit(self._epoch, document_key, self._permit_nonce)

    def invalidate_observation(self) -> None:
        """Any screen change means a new permit must be grounded."""
        with self._lock:
            self._epoch += 1
            self._document_key = None
            self._reobservation_required = True

    def permit_current(self, permit: ActionPermit) -> bool:
        with self._lock:
            return (
                isinstance(permit, ActionPermit)
                and self._owner == InputOwner.AGENT
                and not self._takeover_requested.is_set()
                and not self._reobservation_required
                and type(permit.epoch) is int
                and permit.epoch == self._epoch
                and permit.document_key == self._document_key
                and isinstance(permit.nonce, str)
                and bool(self._permit_nonce)
                and permit.nonce == self._permit_nonce
            )

    def dispatch(self, permit: ActionPermit, operation: Callable[[], T]) -> T:
        """Run one atomic native-operation callback only with current permit.

        Holding the lock prevents an ownership transition from occurring
        mid-callback. An urgent human takeover request is visible before
        lock acquisition; it prevents queued calls from beginning. Input
        stays under the original executor's semantic and safety policies.
        """
        if self._takeover_requested.is_set():
            raise InputDenied("human_takeover_requested")
        with self._lock:
            if not self.permit_current(permit):
                raise InputDenied("stale_or_unverified_input_permit")
            if self._takeover_requested.is_set():
                raise InputDenied("human_takeover_requested")
            return operation()

    @property
    def owner(self) -> InputOwner:
        with self._lock:
            return self._owner

    @property
    def epoch(self) -> int:
        with self._lock:
            return self._epoch

    @property
    def reobservation_required(self) -> bool:
        with self._lock:
            return self._reobservation_required
