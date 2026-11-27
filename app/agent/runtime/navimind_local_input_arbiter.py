"""Local, thread-safe input ownership and stale-plan invalidation.

This is a policy gate for a native desktop input dispatcher, not an OS-wide
mouse/keyboard hook. A host must route ALL agent input through dispatch()
and expose takeover/release controls to the operator. Human takeover signals
intent immediately. An already-running atomic action may finish.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from secrets import token_urlsafe
from threading import Event, Lock, RLock
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
    Native dispatch is serialized separately. A blocked Windows call cannot
    hold the ownership lock or freeze the control panel.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._native_dispatch = Lock()
        self._takeover_requested = Event()
        self._owner = InputOwner.AGENT
        self._epoch = 0
        self._document_key: str | None = None
        self._permit_nonce: str | None = None
        self._reobservation_required = True

    def takeover(self) -> int:
        """Revoke permits immediately without waiting for native code."""
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
            self._permit_nonce = None
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
            self._permit_nonce = None
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

    def _run_native(self, operation: Callable[[], T], validate: Callable[[], bool],
                    denied: str) -> T:
        if self._takeover_requested.is_set():
            raise InputDenied("human_takeover_requested")
        if not self._native_dispatch.acquire(blocking=False):
            raise InputDenied("native_dispatch_in_progress")
        try:
            if not validate():
                raise InputDenied(denied)
            return operation()
        finally:
            self._native_dispatch.release()

    def dispatch(self, permit: ActionPermit, operation: Callable[[], T]) -> T:
        """Run one authorized callback without holding the ownership lock."""
        return self._run_native(
            operation, lambda: self.permit_current(permit), "stale_or_unverified_input_permit",
        )

    def pending_navigation_current(self, epoch: int) -> bool:
        with self._lock:
            return (
                not self._takeover_requested.is_set() and self._owner == InputOwner.AGENT
                and self._epoch == epoch and self._reobservation_required
                and self._document_key is None
            )

    def dispatch_pending_navigation(self, epoch: int, operation: Callable[[], T]) -> T:
        """Authorize the local Start1 activation broker before document proof."""
        return self._run_native(
            operation, lambda: self.pending_navigation_current(epoch), "pending_navigation_epoch_changed",
        )

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
