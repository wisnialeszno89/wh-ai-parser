"""Responsive bounded conversation: LLM text runs off the GUI thread."""
from __future__ import annotations
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import RLock
from typing import Mapping
from app.agent.runtime.navimind_tool_router import (
    ReadOnlyTool, invoke_read_only_tool, parse_model_tool_decision,
    tool_catalog_instructions,
)
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

    def __init__(self, chat: MissionChat, provider: ChatProvider | None,
                 *, runtime_instructions: str = "",
                 read_only_tools: Mapping[str, ReadOnlyTool] | None = None):
        self.chat = chat
        self.provider = provider
        # Trusted host-provided capabilities, never model/user/document asserted.
        # No runtime instructions may grant native actions; local arbiter
        # remains the actual execution authority.
        self.runtime_instructions = runtime_instructions
        self.read_only_tools = dict(read_only_tools or {})
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="navimind-chat")
        self._lock = RLock()
        self._running: Future | None = None
        self._last_error: str | None = None
        self._queued: tuple[int, tuple[tuple[str, str], ...]] | None = None
        self._closed = False
        self._busy = False

    def status(self) -> ConversationStatus:
        with self._lock:
            return ConversationStatus(
                self._busy,
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
            if self._busy:
                # Replace any older pending turn instead of queuing a flood
                # of outdated network calls.
                self._queued = latest
                return True
            self._busy = True
            self._running = self._pool.submit(self._answer_loop, latest)
            return True

    def _answer_loop(self, latest: tuple[int, tuple[tuple[str, str], ...]]) -> None:
        while True:
            try:
                self._answer_in_worker(*latest)
            except Exception:
                with self._lock:
                    self._last_error = "chat_worker_unavailable"
            with self._lock:
                if self._closed or self._queued is None:
                    self._queued = None
                    self._busy = False
                    return
                latest = self._queued
                self._queued = None

    def _answer_in_worker(self, revision: int,
                          transcript: tuple[tuple[str, str], ...]) -> None:
        try:
            instructions = SYSTEM_INSTRUCTIONS + (
                "\n\nSTAN MOŻLIWOŚCI APLIKACJI (ustalony lokalnie przez host):\n"
                + self.runtime_instructions
                if self.runtime_instructions else ""
            )
            if self.read_only_tools:
                instructions += tool_catalog_instructions(self.read_only_tools)
            response = self.provider.reply(
                transcript=transcript, instructions=instructions,
            )
            if self.read_only_tools:
                try:
                    decision = parse_model_tool_decision(
                        response, self.read_only_tools,
                    )
                except ValueError:
                    # Fail closed. Never interpret unstructured model text
                    # as an instruction and never claim an action occurred.
                    answer = (
                        "Nie udało mi się jednoznacznie wybrać narzędzia. "
                        "Nie wykonałem żadnej czynności na komputerze."
                    )
                else:
                    if decision.kind == "tool":
                        # A changed human instruction or closed panel must
                        # invalidate old tool decisions before invocation.
                        with self._lock:
                            current = (not self._closed
                                       and self.chat.snapshot().mission_revision == revision)
                        answer = (
                            invoke_read_only_tool(decision.tool, self.read_only_tools)
                            if current else ""
                        )
                    else:
                        answer = decision.answer
            else:
                answer = response
            if not answer and self.chat.snapshot().mission_revision != revision:
                return
            if not isinstance(answer, str) or not answer.strip():
                raise ChatUnavailable("empty_chat_reply")
            if len(answer) > MissionChat.MAX_MESSAGE_CHARS:
                raise ChatUnavailable("chat_response_too_large")
        except ChatUnavailable as exc:
            with self._lock:
                if self.chat.snapshot().mission_revision == revision:
                    # ChatUnavailable is a trusted, bounded diagnostic code.
                    # Never print an arbitrary server exception or payload.
                    self._last_error = str(exc)
            return
        except Exception:
            with self._lock:
                if self.chat.snapshot().mission_revision == revision:
                    self._last_error = "chat_unexpected_response_error"
            return
        # Do not publish after shutdown. Agent message itself checks
        # mission revision atomically against any concurrent user input.
        with self._lock:
            if self._closed:
                return
            self.chat.agent_message(answer, based_on_revision=revision)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._queued = None
            self._busy = False
        self._pool.shutdown(wait=False, cancel_futures=True)
