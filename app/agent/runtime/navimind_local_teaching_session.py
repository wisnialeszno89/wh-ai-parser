"""Privacy-scoped, manual WindowHub learning in one local session.

This recorder observes human-driven UIA state transitions. It never records
raw customer values, screenshots, native window handles or click coordinates.
Observed effects are guidance, not proof that a certain action caused them.
"""
from __future__ import annotations

from threading import RLock
from app.agent.learning.windowhub_demonstration import (
    semantic_snapshot, semantic_transition, demonstration_experience,
    demonstration_summary,
)


class LocalTeachingSession:
    def __init__(self, *, max_records: int = 64):
        if type(max_records) is not int or not 2 <= max_records <= 128:
            raise ValueError("invalid_teaching_limit")
        self.max_records = max_records
        self._lock = RLock()
        self._active = False
        self._previous = None
        self._records: list[dict] = []
        self._completed: tuple[dict, ...] = ()
        self._summary: dict = {}

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active

    def start(self) -> bool:
        with self._lock:
            if self._active:
                return False
            self._active = True
            self._previous = None
            self._records = []
            self._completed = ()
            self._summary = {}
            return True

    def observe(self, scene) -> bool:
        """Only known WindowHub UIA stages are eligible for manual learning."""
        with self._lock:
            if not self._active:
                return False
            try:
                current = semantic_snapshot(scene)
            except (ValueError, TypeError, AttributeError, KeyError):
                current = None
            if current is None or current.get("stage") in (
                    "windowhub_unmapped", "order_document"):
                self._previous = None
                return False
            previous = self._previous
            self._previous = current
            if previous is None:
                return False
            try:
                transition = semantic_transition(previous, current)
            except (ValueError, TypeError, AttributeError, KeyError):
                return False
            if transition is None:
                return False
            if len(self._records) >= self.max_records:
                # Bounded memory. Stop rather than overwriting earlier
                # demonstration history with an unrelated later sequence.
                self._active = False
                self._previous = None
                self._completed = demonstration_experience(self._records)
                self._summary = demonstration_summary(self._records)
                return False
            self._records.append({"type": "transition", "transition": transition})
            return True

    def finish(self) -> dict:
        with self._lock:
            if self._active:
                self._active = False
                self._previous = None
                self._completed = demonstration_experience(self._records)
                self._summary = demonstration_summary(self._records)
            return dict(self._summary)

    def experience(self) -> tuple[dict, ...]:
        """Advisory only: local V2 policy still validates native actions."""
        with self._lock:
            return tuple(dict(item) for item in self._completed)

    def discard(self) -> None:
        with self._lock:
            self._active = False
            self._previous = None
            self._records = []
            self._completed = ()
            self._summary = {}
