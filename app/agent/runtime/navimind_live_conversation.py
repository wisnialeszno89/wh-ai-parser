"""Responsive bounded conversation: LLM text runs off the GUI thread."""
from __future__ import annotations
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import RLock
from app.agent.runtime.navimind_conversational_provider import (
    ChatProvider, ChatUnavailable, transcript_for_chat, SYSTEM_INSTRUCTIONS,
)
from app.agent.runtime.navimind_mission_chat import MissionChat, MessageRole


@dataclass(frozen=True)
class ConversationStatus:
    active: bool
    latest_revision: int
    last_error: str | None
    provider_connected: bool


class LiveMissionConversation:
    """Text-only replies. Never grants an input permit or edits an offer."""

    def __init__(self, chat: MissionChat, provider: ChatProvider | None):
        self.chat = chat
        self.provider = provider
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="navimind-chat")
        self._lock = RLock()
        self._running: Future | None = None
        self._last_error: str | None = None
        self._queued: tuple[int, tuple[tuple[str, str], ...]] | None = None
        self._closed = False

    def status(self) -> ConversationStatus:
        with self._lock:
            return ConversationStatus(
                bool(self._running is not None and not self._running.done()),
                self.chat.snapshot().mission_revision, self._last_error,
                self.provider is not None,
            )

    def submit_current_message(self, message_id: int) -> bool:
        with self._lock:
            if self._closed or self.provider is None:
                self._last_error = "chat_provider_not_configured"
                return False
            snapshot = self.chat.snapshot()
            if not any(
                m.message_id == message_id and m.role == MessageRole.HUMAN
                and m.mission_revision == snapshot.mission_revision
                for m in snapshot.messages
            ):
                self._last_error = "stale_or_nonhuman_chat_message"
                return False
            self._last_error = None
            latest = (snapshot.mission_revision, transcript_for_chat(snapshot))
            if self._running is not None and not self._running.done():
                # Replace any older pending turn instead of queuing a flood
                # of outdated network calls.
                self._queued = latest
                return True
            self._running = self._pool.submit(self._answer_loop, latest)
            return True

    def _answer_loop(self, latest: tuple[int, tuple[tuple[str, str], ...]]) -> None:
        while True:
            self._answer_in_worker(*latest)
            with self._lock:
                if self._closed or self._queued is None:
                    self._queued = None
                    return
                latest = self._queued
                self._queued = None

    def _answer_in_worker(self, revision: int,
                          transcript: tuple[tuple[str, str], ...]) -> None:
        try:
            answer = self.provider.reply(
                transcript=transcript, instructions=SYSTEM_INSTRUCTIONS,
            )
            if not isinstance(answer, str) or not answer.strip():
                raise ChatUnavailable("empty_chat_reply")
            if len(answer) > MissionChat.MAX_MESSAGE_CHARS:
                raise ChatUnavailable("chat_response_too_large")
        except Exception:
            with self._lock:
                if self.chat.snapshot().mission_revision == revision:
                    self._last_error = "chat_model_unavailable_or_invalid_response"
            return
        # Agent message has its own atomic revision check.
        self.chat.agent_message(answer, based_on_revision=revision)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._queued = None
        self._pool.shutdown(wait=False, cancel_futures=True)
