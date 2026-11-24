"""Async agent dialogue: old answers discarded and quick edits coalesced."""
from __future__ import annotations

from threading import Event
import time

from app.agent.runtime.navimind_live_conversation import LiveMissionConversation
from app.agent.runtime.navimind_local_input_arbiter import InputOwner, LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat


class Provider:
    def __init__(self):
        self.calls = []
        self.entered = Event()
        self.release = Event()

    def reply(self, *, transcript, instructions):
        self.calls.append(transcript)
        self.entered.set()
        self.release.wait(timeout=3)
        return "Przygotuję propozycję bez zapisywania oferty."


def create():
    gate = LocalInputArbiter()
    chat = MissionChat(document_key="OFR/101", arbiter=gate)
    return chat, gate


def await_idle(engine):
    limit = time.monotonic() + 4
    while engine.status().active and time.monotonic() < limit:
        time.sleep(0.005)
    assert not engine.status().active


def test_no_provider_returns_disconnected_without_worker_request():
    chat, _ = create()
    engine = LiveMissionConversation(chat, None)
    m = chat.user_message("Zrób ofertę")
    assert engine.submit_current_message(m.message_id) is False
    assert engine.status().last_error == "chat_provider_not_configured"
    engine.close()


def test_valid_async_answer_is_visible_and_does_not_resume_native_actions():
    chat, gate = create()
    provider = Provider()
    engine = LiveMissionConversation(chat, provider)
    msg = chat.user_message("Zmień parapet")
    assert engine.submit_current_message(msg.message_id)
    assert provider.entered.wait(2)
    assert engine.status().active
    provider.release.set()
    await_idle(engine)
    assert chat.snapshot().messages[-1].text.startswith("Przygotuję")
    assert gate.owner == InputOwner.HUMAN
    assert chat.snapshot().requires_replan
    engine.close()


def test_new_message_suppresses_old_model_reply_and_answers_latest():
    chat, _ = create()
    provider = Provider()
    engine = LiveMissionConversation(chat, provider)
    first = chat.user_message("Dodaj drzwi")
    assert engine.submit_current_message(first.message_id)
    assert provider.entered.wait(2)
    second = chat.user_message("Jednak dodaj też panel EK-02-A")
    assert engine.submit_current_message(second.message_id)
    provider.release.set()
    await_idle(engine)
    assert len(provider.calls) == 2
    assert "Jednak dodaj" in repr(provider.calls[-1])
    agent_replies = [m for m in chat.snapshot().messages if m.role.value == "agent"]
    assert len(agent_replies) == 1
    assert agent_replies[0].mission_revision == 2
    engine.close()


def test_rapid_messages_replace_queued_old_requests():
    chat, _ = create()
    provider = Provider()
    engine = LiveMissionConversation(chat, provider)
    a = chat.user_message("Instrukcja A")
    engine.submit_current_message(a.message_id)
    assert provider.entered.wait(2)
    b = chat.user_message("Instrukcja B")
    engine.submit_current_message(b.message_id)
    c = chat.user_message("Instrukcja C")
    engine.submit_current_message(c.message_id)
    provider.release.set()
    await_idle(engine)
    assert len(provider.calls) == 2
    assert "Instrukcja C" in repr(provider.calls[-1])
    engine.close()


def test_closing_while_request_in_flight_blocks_late_reply():
    chat, _ = create()
    provider = Provider()
    engine = LiveMissionConversation(chat, provider)
    m = chat.user_message("Pierwsza instrukcja")
    engine.submit_current_message(m.message_id)
    assert provider.entered.wait(2)
    engine.close()
    provider.release.set()
    deadline = time.monotonic() + 2
    while len(provider.calls) == 0 and time.monotonic() < deadline:
        time.sleep(0.01)
    time.sleep(0.03)
    assert not any(x.role.value == "agent" for x in chat.snapshot().messages)


def test_rejects_old_human_message_id_without_model_request():
    chat, _ = create()
    provider = Provider()
    engine = LiveMissionConversation(chat, provider)
    a = chat.user_message("Pierwsza")
    chat.user_message("Druga")
    assert not engine.submit_current_message(a.message_id)
    assert provider.calls == []
    engine.close()


def test_rejects_agent_message_as_if_it_were_human_instruction():
    chat, _ = create()
    engine = LiveMissionConversation(chat, Provider())
    chat.user_message("Cześć")
    answer = chat.agent_message("Witaj", based_on_revision=1)
    assert not engine.submit_current_message(answer.message_id)
    engine.close()


def test_closing_prevents_new_requests():
    chat, _ = create()
    engine = LiveMissionConversation(chat, Provider())
    engine.close()
    m = chat.user_message("Nowe zadanie")
    assert not engine.submit_current_message(m.message_id)
