"""Model-driven capability choice: host allowlist is the final authority."""
import pytest

from app.agent.runtime.navimind_live_conversation import LiveMissionConversation
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter, InputOwner
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_tool_router import (
    ReadOnlyTool, invoke_read_only_tool, parse_model_tool_decision,
    tool_catalog_instructions,
)

import time


def wait(engine):
    deadline = time.monotonic() + 4
    while engine.status().active and time.monotonic() < deadline:
        time.sleep(.005)
    assert not engine.status().active


def new_chat():
    gate = LocalInputArbiter()
    return MissionChat(document_key="disposable-offer", arbiter=gate), gate


def tools(fn):
    return {
        "find_windowhub": ReadOnlyTool(
            "find_windowhub", "Wyszukaj uruchomiony WindowHub", fn,
        ),
        "engine_capabilities": ReadOnlyTool(
            "engine_capabilities", "Sprawdź funkcje NaviMind", lambda: "Dostępne: obserwacja",
        ),
    }


@pytest.mark.parametrize("response", [
    '{"kind":"tool","tool":"click"}',
    '{"kind":"tool","tool":"find_windowhub","command":"powershell"}',
    '{"kind":"tool","tool":"__import__"}',
    '{"kind":"tool","tool":123}',
    '{"kind":"answer","answer":"Tak","tool":"find_windowhub"}',
    'tekst zamiast JSON',
    '["find_windowhub"]',
])
def test_model_cannot_execute_nonallowlisted_or_malformed_action(response):
    with pytest.raises(ValueError):
        parse_model_tool_decision(response, tools(lambda: "FOUND"))


def test_model_chooses_local_tool_and_reports_actual_result():
    calls = []
    class Provider:
        def reply(self, *, transcript, instructions):
            assert "find_windowhub" in instructions
            assert "engine_capabilities" in instructions
            assert transcript[-1][0] == "user"
            return '{"kind":"tool","tool":"find_windowhub"}'
    chat, gate = new_chat()
    engine = LiveMissionConversation(
        chat, Provider(),
        read_only_tools=tools(lambda: calls.append("observed") or
                              "Znalazłem WindowHub w tle; nie kliknąłem niczego."),
    )
    msg = chat.user_message("Czy WH jest uruchomiony? Sprawdź mi go na komputerze.")
    assert engine.submit_current_message(msg.message_id)
    wait(engine)
    assert calls == ["observed"]
    assert chat.snapshot().messages[-1].text.startswith("Znalazłem WindowHub")
    assert gate.owner == InputOwner.HUMAN
    engine.close()


def test_model_chooses_normal_answer_without_invoking_tools():
    calls = []
    class Provider:
        def reply(self, *, transcript, instructions):
            return '{"kind":"answer","answer":"Dzień dobry! Co przygotowujemy?"}'
    chat, _ = new_chat()
    engine = LiveMissionConversation(chat, Provider(), read_only_tools=tools(
        lambda: calls.append("unexpected") or "FOUND",
    ))
    msg = chat.user_message("Cześć")
    assert engine.submit_current_message(msg.message_id)
    wait(engine)
    assert calls == []
    assert "Dzień dobry" in chat.snapshot().messages[-1].text
    engine.close()


def test_invalid_model_decision_fails_closed_without_dispatch():
    calls = []
    class Provider:
        def reply(self, *, transcript, instructions):
            return '{"kind":"tool","tool":"delete_windows"}'
    chat, _ = new_chat()
    engine = LiveMissionConversation(chat, Provider(), read_only_tools=tools(
        lambda: calls.append("unexpected") or "FOUND",
    ))
    msg = chat.user_message("Usuń wszystkie pliki Windows")
    assert engine.submit_current_message(msg.message_id)
    wait(engine)
    assert calls == []
    assert "Nie wykonałem" in chat.snapshot().messages[-1].text
    engine.close()


def test_tool_failure_does_not_leak_private_exception():
    def private_failure():
        raise RuntimeError("Tajna nazwa kontrahenta 987654")
    reply = invoke_read_only_tool("find_windowhub", tools(private_failure))
    assert "987654" not in reply
    assert "Nie udało" in reply


def test_model_cannot_inject_custom_tool_arguments_or_path():
    denied = '{"kind":"tool","tool":"find_windowhub","path":"C:/private"}'
    with pytest.raises(ValueError):
        parse_model_tool_decision(denied, tools(lambda: "FOUND"))


def test_engine_tool_catalog_has_no_native_action_authority():
    catalog = tool_catalog_instructions(tools(lambda: "FOUND"))
    assert "find_windowhub" in catalog
    assert "uruchamiania aplikacji" in catalog
    assert "klikania" in catalog
    assert "powershell.exe" not in catalog.lower()


def test_stale_model_tool_decision_does_not_execute_tool():
    from threading import Event
    entered, release = Event(), Event()
    calls = []
    class Provider:
        def reply(self, *, transcript, instructions):
            entered.set()
            release.wait(2)
            return '{"kind":"tool","tool":"find_windowhub"}'
    chat, _ = new_chat()
    engine = LiveMissionConversation(chat, Provider(), read_only_tools=tools(
        lambda: calls.append("wrong") or "FOUND",
    ))
    old = chat.user_message("Znajdź WH")
    assert engine.submit_current_message(old.message_id)
    assert entered.wait(1)
    chat.user_message("Anuluj, nie sprawdzaj")
    release.set()
    wait(engine)
    assert calls == []
    engine.close()


def test_intake_metadata_tool_is_exposed_but_never_customer_content():
    from pathlib import Path
    from app.agent.runtime.navimind_enquiry_inbox import LocalEnquiryInbox
    inbox = LocalEnquiryInbox()
    inbox.set_text("Sekret kontrahenta: TOP TRANS / cena 123456")
    status = inbox.status()
    assert status["has_enquiry"] is True
    assert status["transmitted_to_model"] is False
    host_source = (Path(__file__).resolve().parents[1] / "tools" /
                   "run_navimind_shared_control_center.py").read_text(encoding="utf-8")
    assert '"enquiry_status": ReadOnlyTool(' in host_source
    assert 'status = intake.status()' in host_source
    assert "intake.preview()" not in host_source
    assert "read_only_tools=tool_registry" in host_source


def test_model_can_select_capability_catalog_without_exec():
    calls = []
    class Provider:
        def reply(self, *, transcript, instructions):
            return '{"kind":"tool","tool":"engine_capabilities"}'
    chat, _ = new_chat()
    engine = LiveMissionConversation(chat, Provider(), read_only_tools=tools(
        lambda: calls.append("wrong") or "FOUND",
    ))
    message = chat.user_message("Co potrafisz wykonać na Windows?")
    assert engine.submit_current_message(message.message_id)
    wait(engine)
    assert "Dostępne: obserwacja" in chat.snapshot().messages[-1].text
    assert calls == []
    engine.close()
