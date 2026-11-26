"""Regression tests: malformed chat tool JSON must not lose local results."""
import time

from app.agent.runtime.navimind_live_conversation import (
    LiveMissionConversation, explicit_offer_plan_request,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_tool_router import ReadOnlyTool


def idle(engine):
    deadline = time.monotonic() + 3.5
    while engine.status().active and time.monotonic() < deadline:
        time.sleep(0.005)
    assert not engine.status().active


def chat():
    return MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())


class BadJson:
    def reply(self, *, transcript, instructions):
        return "Pracuję nad tym. Nie jest to JSON."


class FirstToolThenBadJson:
    def __init__(self):
        self.calls = 0

    def reply(self, *, transcript, instructions):
        self.calls += 1
        if self.calls == 1:
            return '{"kind":"tool","tool":"inspect_windowhub"}'
        return "Nieprawidłowy JSON"


def test_explicit_offer_request_not_general_status_or_negation():
    assert explicit_offer_plan_request(
        "Na podstawie zapytania wybierz Top Trans i stwórz ofertę "
        "bez montażu, demontażu i wykończenia, rabat 15%"
    )
    assert not explicit_offer_plan_request("Czy widzisz WindowHub?")
    assert not explicit_offer_plan_request("Nie twórz oferty, tylko sprawdź klienta")


def test_invalid_gateway_json_falls_back_to_local_safe_offer_planner():
    mission = chat()
    calls = []
    engine = LiveMissionConversation(
        mission, BadJson(),
        read_only_tools={
            "prepare_windowhub_work": ReadOnlyTool(
                "prepare_windowhub_work", "Plan only",
                lambda: calls.append(1) or
                "Zatrzymano: wymagane udostępnienie dokumentu.",
            )
        },
        allow_tool_chaining=True,
    )
    msg = mission.user_message(
        "Stwórz ofertę dla Top Trans bez montażu, rabat 15%"
    )
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == [1]
    assert "wymagane udostępnienie" in mission.snapshot().messages[-1].text
    engine.close()


def test_read_only_observation_survives_bad_json_after_tool_result():
    mission = chat()
    calls = []
    provider = FirstToolThenBadJson()
    engine = LiveMissionConversation(
        mission, provider,
        read_only_tools={
            "inspect_windowhub": ReadOnlyTool(
                "inspect_windowhub", "Observe only",
                lambda: calls.append(1) or
                "WindowHub Start1 jest otwarty w tle. Nic nie kliknięto.",
            )
        },
        allow_tool_chaining=True,
    )
    msg = mission.user_message("Sprawdź WindowHub w tle")
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == [1]
    assert "WindowHub Start1" in mission.snapshot().messages[-1].text
    engine.close()


class GenericAnswerInsteadOfPlan:
    def reply(self, *, transcript, instructions):
        if any("[WYNIK ZAUFANEGO LOKALNEGO NARZĘDZIA" in value
               for _, value in transcript):
            return '{"kind":"answer","answer":"Stan sprawdzony: brak konfiguracji V2."}'
        return '{"kind":"answer","answer":"Proponuję sprawdzić program i przygotować plan."}'


def test_explicit_offer_plan_bypasses_generic_model_answer():
    mission = chat()
    calls = []
    engine = LiveMissionConversation(
        mission, GenericAnswerInsteadOfPlan(),
        read_only_tools={
            "prepare_windowhub_work": ReadOnlyTool(
                "prepare_windowhub_work", "Plan only",
                lambda: calls.append(1) or
                "Znalazłem WindowHub, ale V2 nie jest skonfigurowane.",
            )
        },
        allow_tool_chaining=True,
    )
    msg = mission.user_message(
        "Przygotuj nową ofertę dla Top Trans na podstawie zapytania. "
        "Nie wykonuj kliknięć."
    )
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == [1]
    assert "brak konfiguracji V2" in mission.snapshot().messages[-1].text
    engine.close()


def test_plain_question_does_not_force_offer_planner():
    mission = chat()
    calls = []
    engine = LiveMissionConversation(
        mission, GenericAnswerInsteadOfPlan(),
        read_only_tools={
            "prepare_windowhub_work": ReadOnlyTool(
                "prepare_windowhub_work", "Plan only",
                lambda: calls.append(1) or "Nie powinienem zostać wywołany",
            )
        },
        allow_tool_chaining=True,
    )
    msg = mission.user_message("Co oznacza rabat 15%?")
    assert engine.submit_current_message(msg.message_id)
    idle(engine)
    assert calls == []
    engine.close()
