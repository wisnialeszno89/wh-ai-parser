"""Live user-message inbox with explicit, versioned mission changes.

Pure, local state machine. Messages can be submitted while an agent reasons;
they invalidate stale action authority immediately via human takeover.
No language model, network, desktop IO, or autonomous editing is invoked.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import Callable

from app.agent.runtime.navimind_local_input_arbiter import InputOwner, LocalInputArbiter


class MessageRole(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class ChangeState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass(frozen=True)
class ChatMessage:
    message_id: int
    role: MessageRole
    text: str
    mission_revision: int


@dataclass(frozen=True)
class RevisionRequest:
    request_id: int
    originating_message_id: int
    document_key: str
    proposed_change: str
    revision: int
    state: ChangeState = ChangeState.PENDING


@dataclass(frozen=True)
class ChatState:
    mission_revision: int
    messages: tuple[ChatMessage, ...]
    changes: tuple[RevisionRequest, ...]
    requires_replan: bool


class MissionChat:
    """Inbox deliberately separates what a user said from what agent may do.

    Each user instruction increments revision and invalidates queued actions.
    Explicitly approved structured changes become inputs for a future verified
    replan. Existing files are NEVER changed by this component.
    """
    MAX_MESSAGE_CHARS = 4000
    MAX_MESSAGES = 300
    MAX_CHANGES = 100

    def __init__(self, *, document_key: str,
                 arbiter: LocalInputArbiter,
                 on_takeover: Callable[[], None] | None = None):
        if not isinstance(document_key, str) or not document_key.strip():
            raise ValueError("chat_requires_pinned_document")
        self.document_key = document_key
        self.arbiter = arbiter
        self.on_takeover = on_takeover
        self._lock = RLock()
        self._revision = 0
        self._messages: list[ChatMessage] = []
        self._changes: list[RevisionRequest] = []

    def snapshot(self) -> ChatState:
        with self._lock:
            return ChatState(
                self._revision, tuple(self._messages),
                tuple(self._changes), (
                    any(m.role == MessageRole.HUMAN and m.mission_revision == self._revision
                        for m in self._messages)
                    or any(c.state in (ChangeState.PENDING, ChangeState.APPROVED)
                           and c.revision == self._revision for c in self._changes)
                ),
            )

    def _append(self, role: MessageRole, text: str) -> ChatMessage:
        if len(self._messages) >= self.MAX_MESSAGES:
            raise ValueError("chat_message_limit_reached")
        message = ChatMessage(
            message_id=len(self._messages) + 1,
            role=role, text=text, mission_revision=self._revision,
        )
        self._messages.append(message)
        return message

    def user_message(self, text: str) -> ChatMessage:
        """First revoke old plan, then append new user instructions.

        This is conservative: even a simple question invalidates the current
        plan until an operator/agent explicitly resumes. Future intent
        recognition may distinguish safe information-only questions.
        """
        if not isinstance(text, str) or not text.strip() or len(text) > self.MAX_MESSAGE_CHARS:
            raise ValueError("invalid_chat_message")
        with self._lock:
            if len(self._messages) >= self.MAX_MESSAGES:
                raise ValueError("chat_message_limit_reached")
            if self.on_takeover is not None:
                self.on_takeover()
            elif self.arbiter.owner != InputOwner.HUMAN:
                self.arbiter.takeover()
            self._revision += 1
            return self._append(MessageRole.HUMAN, text.strip())

    def agent_message(self, text: str, *, based_on_revision: int) -> ChatMessage | None:
        """A slow model reply from an older mission revision is discarded."""
        with self._lock:
            if based_on_revision != self._revision:
                return None
            if not isinstance(text, str) or not text.strip() or len(text) > self.MAX_MESSAGE_CHARS:
                raise ValueError("invalid_agent_message")
            return self._append(MessageRole.AGENT, text.strip())

    def propose_change(self, *, originating_message_id: int,
                       proposed_change: str, expected_revision: int) -> RevisionRequest:
        """Trusted planner must derive an explicit proposed change.

        Free-text user input is never executable and never auto-interpreted
        as a price, dimension, deletion or customer switch.
        """
        with self._lock:
            if expected_revision != self._revision:
                raise ValueError("stale_chat_revision")
            if not isinstance(proposed_change, str) or not proposed_change.strip() or len(proposed_change) > 2000:
                raise ValueError("invalid_change_proposal")
            if len(self._changes) >= self.MAX_CHANGES:
                raise ValueError("change_limit_reached")
            if not any(
                msg.message_id == originating_message_id
                and msg.role == MessageRole.HUMAN
                and msg.mission_revision == self._revision
                for msg in self._messages
            ):
                raise ValueError("proposal_must_reference_current_human_message")
            request = RevisionRequest(
                request_id=len(self._changes) + 1,
                originating_message_id=originating_message_id,
                document_key=self.document_key,
                proposed_change=proposed_change.strip(),
                revision=self._revision,
            )
            self._changes.append(request)
            return request

    def approve_change(self, request_id: int, *, expected_revision: int,
                       approved: bool) -> RevisionRequest:
        with self._lock:
            if type(expected_revision) is not int or self._revision != expected_revision:
                raise ValueError("stale_chat_revision")
            if type(approved) is not bool:
                raise ValueError("explicit_review_required")
            if type(request_id) is not int or request_id <= 0 or request_id > len(self._changes):
                raise ValueError("unknown_revision_request")
            current = self._changes[request_id - 1]
            if current.state != ChangeState.PENDING or current.revision != self._revision:
                raise ValueError("change_already_decided_or_stale")
            updated = RevisionRequest(
                current.request_id, current.originating_message_id,
                current.document_key, current.proposed_change,
                current.revision,
                ChangeState.APPROVED if approved else ChangeState.REJECTED,
            )
            self._changes[request_id - 1] = updated
            return updated

    def approved_for_replan(self, *, expected_revision: int) -> tuple[RevisionRequest, ...]:
        with self._lock:
            if expected_revision != self._revision:
                raise ValueError("stale_chat_revision")
            return tuple(c for c in self._changes
                         if c.revision == self._revision and c.state == ChangeState.APPROVED)

    def mark_applied(self, request_id: int, *, expected_revision: int,
                     independently_verified: bool) -> RevisionRequest:
        """Only postcondition readback can mark an approved change completed."""
        with self._lock:
            if type(independently_verified) is not bool or not independently_verified:
                raise ValueError("independent_postcondition_required")
            if expected_revision != self._revision:
                raise ValueError("stale_chat_revision")
            if type(request_id) is not int or request_id <= 0 or request_id > len(self._changes):
                raise ValueError("unknown_revision_request")
            current = self._changes[request_id - 1]
            if current.state != ChangeState.APPROVED or current.revision != self._revision:
                raise ValueError("approved_current_change_required")
            updated = RevisionRequest(
                current.request_id, current.originating_message_id,
                current.document_key, current.proposed_change,
                current.revision, ChangeState.APPLIED,
            )
            self._changes[request_id - 1] = updated
            return updated
