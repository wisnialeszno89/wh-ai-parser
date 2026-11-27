"""Host facts and right-click history copying remain available across changes."""
from pathlib import Path
import time

from app.agent.runtime.navimind_live_conversation import (
    LiveMissionConversation, explicit_local_mission_status_request,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_tool_router import ReadOnlyTool

ROOT = Path(__file__).resolve().parents[1]


def test_explicit_mission_status_intent():
    assert explicit_local_mission_status_request(
        "NaviMind, wyjaśnij na podstawie rzeczywistego stanu lokalnych narzędzi, "
        "co zostało wykonane, czego jeszcze nie wykonano i jakie zatwierdzenie będzie "
        "konieczne przed pierwszym sterowaniem WindowHub."
    )
    assert explicit_local_mission_status_request(
        "Podaj status misji"
    )
    assert not explicit_local_mission_status_request(
        "Przygotuj ofertę dla klienta."
    )


def test_status_is_from_local_host_even_if_model_is_unavailable():
    class NeverCallProvider:
        def reply(self, **kwargs):
            raise AssertionError("status must not require remote model")

    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    calls = []
    engine = LiveMissionConversation(
        chat, NeverCallProvider(),
        read_only_tools={
            "mission_status": ReadOnlyTool(
                "mission_status", "Read only local status",
                lambda: calls.append(True) or
                "WindowHub: znaleziony. V2: v2_endpoint_missing.",
            )
        },
    )
    msg = chat.user_message("Wyjaśnij rzeczywisty stan lokalnych narzędzi")
    assert engine.submit_current_message(msg.message_id)
    deadline = time.monotonic() + 5
    while engine.status().active and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not engine.status().active
    assert calls == [True]
    assert "v2_endpoint_missing" in chat.snapshot().messages[-1].text
    engine.close()


def test_mouse_copy_history_and_last_reply_buttons():
    source = (ROOT / "tools/navimind_main_workspace.py").read_text(encoding="utf-8")
    assert 'self.history.bind("<Button-3>", show)' in source
    assert "Kopiuj zaznaczenie" in source
    assert "Kopiuj ostatnią odpowiedź" in source
    assert "Zaznacz całą rozmowę" in source
    assert 'self.history.get("sel.first", "sel.last")' in source
    assert "self.clipboard_append(content)" in source
    assert "if message.role == MessageRole.AGENT" in source
    assert "self._install_history_copy_menu()" in source


def test_local_status_tool_is_read_only():
    source = (ROOT / "tools/run_navimind_shared_control_center.py").read_text(
        encoding="utf-8"
    )
    assert '"mission_status": ReadOnlyTool(' in source
    assert "def verified_mission_status()" in source
    assert "discover_windowhub_read_only()" in source
    assert "background_work._v2_configuration_blocker()" in source


def test_status_queries_about_creation_or_approval_are_host_routed():
    assert explicit_local_mission_status_request(
        "Powiedz, czy utworzono i zapisano ofertę w WindowHub. "
        "Wskaż dokładnie, czego brakuje do rozpoczęcia sterowania."
    )
    assert explicit_local_mission_status_request(
        "Jakie zatwierdzenie będzie konieczne przed pierwszym sterowaniem?"
    )


def test_status_does_not_conflate_endpoint_configuration_with_operator_consent():
    code = (ROOT / "tools/run_navimind_shared_control_center.py").read_text(
        encoding="utf-8"
    )
    assert "Konfiguracja adresu V2 i sekretu to czynność techniczna" in code
    assert "NIE zgoda handlowca" in code
    assert "Potwierdzone wykluczenia usług/opcji" in code
    assert "udany test" in code
    assert "Nie mam potwierdzenia utworzenia ani zapisania oferty" in code
