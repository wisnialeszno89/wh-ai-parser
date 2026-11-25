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


def test_gateway_failure_reason_is_preserved_without_unsafe_raw_text():
    from app.agent.runtime.navimind_conversational_provider import ChatUnavailable

    class FailingProvider:
        def reply(self, *, transcript, instructions):
            raise ChatUnavailable("chat_authentication_failed_401")

    chat, _ = create()
    engine = LiveMissionConversation(chat, FailingProvider())
    msg = chat.user_message("Czy możesz mi odpowiedzieć?")
    assert engine.submit_current_message(msg.message_id)
    await_idle(engine)
    assert engine.status().last_error == "chat_authentication_failed_401"
    assert not any(x.role.value == "agent" for x in chat.snapshot().messages)
    engine.close()


def test_unexpected_gateway_error_is_generic():
    class FailingProvider:
        def reply(self, *, transcript, instructions):
            raise RuntimeError("DO_NOT_SHOW_SECRET")

    chat, _ = create()
    engine = LiveMissionConversation(chat, FailingProvider())
    msg = chat.user_message("Cześć")
    assert engine.submit_current_message(msg.message_id)
    await_idle(engine)
    assert engine.status().last_error == "chat_unexpected_response_error"
    engine.close()


def test_trusted_windows_host_capabilities_reach_model_as_instructions():
    captured = []
    class ProviderWithSpy:
        def reply(self, *, transcript, instructions):
            captured.append(instructions)
            return "Mam obserwator, ale wykonawca V2 nie jest podłączony."
    chat, gate = create()
    engine = LiveMissionConversation(
        chat, ProviderWithSpy(),
        runtime_instructions="HOST_CONFIRMED_READ_ONLY=True; V2_EXECUTOR=False",
    )
    message = chat.user_message("Czy możesz pracować w WindowHub?")
    assert engine.submit_current_message(message.message_id)
    await_idle(engine)
    assert len(captured) == 1
    assert "HOST_CONFIRMED_READ_ONLY=True" in captured[0]
    assert "V2_EXECUTOR=False" in captured[0]
    assert gate.owner == InputOwner.HUMAN
    engine.close()


def test_default_conversation_does_not_invent_capability_context():
    captured = []
    class ProviderWithSpy:
        def reply(self, *, transcript, instructions):
            captured.append(instructions)
            return "Nie wykonano działania."
    chat, _ = create()
    engine = LiveMissionConversation(chat, ProviderWithSpy())
    message = chat.user_message("Cześć")
    assert engine.submit_current_message(message.message_id)
    await_idle(engine)
    assert "STAN MOŻLIWOŚCI APLIKACJI" not in captured[0]
    engine.close()


def test_launcher_explicitly_discloses_nonexecuting_windows_capability():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "tools" /
              "run_navimind_shared_control_center.py").read_text(encoding="utf-8")
    assert "runtime_instructions=runtime_instructions" in source
    assert "wykonawca V2 NIE jest podłączony" in source
    assert "NAVIMIND_V2_EXECUTOR_CONNECTED=False" in source


def test_document_context_requires_explicit_approval_and_revocation():
    captured = []
    class DocumentProvider:
        def reply(self, *, transcript, instructions):
            captured.append((transcript, instructions))
            return '{"kind":"answer","answer":"W dokumencie: VEKA Softline, 990 x 920 mm."}'
    from app.agent.runtime.navimind_tool_router import ReadOnlyTool
    chat, _ = create()
    engine = LiveMissionConversation(
        chat, DocumentProvider(),
        read_only_tools={"engine_capabilities": ReadOnlyTool(
            "engine_capabilities", "pokaż możliwości", lambda: "tylko odczyt",
        )},
    )
    first = chat.user_message("Czy widzisz PDF?")
    assert engine.submit_current_message(first.message_id)
    await_idle(engine)
    assert all("TAJNE-DANE-999" not in repr(t) for t, _ in captured)

    engine.approve_document_context(
        "NIEZAUFANE DANE Z DOKUMENTU\nVEKA Softline "
        "990 x 920 mm TAJNE-DANE-999"
    )
    assert engine.document_context_active()
    second = chat.user_message("Przeanalizuj udostępniony PDF")
    assert engine.submit_current_message(second.message_id)
    await_idle(engine)
    assert any("TAJNE-DANE-999" in item[1] for item in captured[-1][0])
    assert captured[-1][0][-1][1] == "Przeanalizuj udostępniony PDF"
    assert "niezaufane dane" in captured[-1][1].casefold()

    engine.revoke_document_context()
    assert not engine.document_context_active()
    third = chat.user_message("Cześć, już bez PDF")
    assert engine.submit_current_message(third.message_id)
    await_idle(engine)
    assert all("TAJNE-DANE-999" not in item[1] for item in captured[-1][0])
    engine.close()


def test_invalid_document_context_is_not_approved():
    chat, _ = create()
    engine = LiveMissionConversation(chat, Provider())
    import pytest
    with pytest.raises(ValueError):
        engine.approve_document_context("x" * 5000)
    assert not engine.document_context_active()
    engine.close()
