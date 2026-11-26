"""Human service corrections are conversational constraints, not native actions."""
import time

from app.agent.runtime.navimind_live_conversation import (
    LiveMissionConversation, explicit_service_exclusion_correction,
)
from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat


def test_standalone_service_exclusions():
    assert explicit_service_exclusion_correction(
        "bez montazu, demontazu i wykonczenia"
    ) == ("montaż", "demontaż", "wykończenie")
    assert explicit_service_exclusion_correction(
        "Bez montażu, demontażu i wykończenia."
    ) == ("montaż", "demontaż", "wykończenie")
    assert explicit_service_exclusion_correction("bez montażu") == ("montaż",)
    assert explicit_service_exclusion_correction(
        "bez montażu, ustaw rabat 15%"
    ) == ()
    assert explicit_service_exclusion_correction("zapisz ofertę") == ()


def test_simple_correction_never_calls_remote_model_or_native_tool():
    class MustNotCall:
        def reply(self, **kwargs):
            raise AssertionError("model must not be used for bounded correction")

    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    engine = LiveMissionConversation(chat, MustNotCall())
    msg = chat.user_message("bez montazu, demontazu i wykonczenia")
    assert engine.submit_current_message(msg.message_id)
    deadline = time.monotonic() + 5
    while engine.status().active and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not engine.status().active
    latest = chat.snapshot().messages[-1].text
    assert "Przyjąłem korektę" in latest
    assert "Nie zmieniłem jeszcze oferty" in latest
    engine.close()


def test_next_offer_mission_inherits_immediate_service_correction():
    from app.agent.runtime.navimind_work_mission import (
        WorkMissionCoordinator, bounded_v2_mission_goal,
    )

    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    chat.user_message("Stwórz ofertę dla klienta testowego.")
    chat.user_message("bez montażu, demontażu i wykończenia")
    chat.user_message("Zrób wycenę dla bieżącego klienta")
    mission = WorkMissionCoordinator(chat).queue_current()
    assert mission is not None
    assert mission.goal == "Zrób wycenę dla bieżącego klienta"
    assert mission.service_exclusions == ("montaż", "demontaż", "wykończenie")
    assert "Nie uwzględniaj: montaż, demontaż, wykończenie" in (
        bounded_v2_mission_goal(mission)
    )


def test_unrelated_turn_breaks_automatic_constraint_inheritance():
    from app.agent.runtime.navimind_work_mission import WorkMissionCoordinator

    chat = MissionChat(document_key="DRAFT/NEW", arbiter=LocalInputArbiter())
    chat.user_message("bez montażu")
    chat.user_message("Podaj dzisiejszy status")
    chat.user_message("Zrób nową ofertę")
    mission = WorkMissionCoordinator(chat).queue_current()
    assert mission is not None
    assert mission.service_exclusions == ()
