"""Regression tests for real-time inbox, approved changes and stale replies."""
import pytest

from app.agent.runtime.navimind_local_input_arbiter import InputOwner, LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import (
    ChangeState, MessageRole, MissionChat,
)


def setup_chat():
    gate = LocalInputArbiter()
    return MissionChat(document_key="OFR/101", arbiter=gate), gate


def test_message_arriving_during_work_invalidates_old_execution_permit():
    chat, gate = setup_chat()
    original = gate.observe_document("OFR/101")
    message = chat.user_message("Zmień kolor pozycji 3 na antracyt")
    assert message.role == MessageRole.HUMAN
    assert message.mission_revision == 1
    assert gate.owner == InputOwner.HUMAN
    assert not gate.permit_current(original)


def test_stale_agent_reply_after_user_change_is_dropped():
    chat, _ = setup_chat()
    chat.user_message("Zmień szerokość")
    assert chat.agent_message("Stara propozycja", based_on_revision=0) is None
    assert len(chat.snapshot().messages) == 1
    response = chat.agent_message("Zaproponuję zmianę po sprawdzeniu oferty.",
                                  based_on_revision=1)
    assert response is not None
    assert response.role == MessageRole.AGENT


def test_pending_request_is_not_approval_or_direct_action():
    chat, _ = setup_chat()
    original = chat.user_message("Popraw opis")
    change = chat.propose_change(
        originating_message_id=original.message_id,
        proposed_change="Pozycja 1: uzupełnić opis",
        expected_revision=1,
    )
    assert change.state == ChangeState.PENDING
    assert chat.approved_for_replan(expected_revision=1) == ()
    assert chat.snapshot().requires_replan


def test_approval_is_explicit_and_requires_independent_readback():
    chat, _ = setup_chat()
    msg = chat.user_message("Nowa cena pozycji 2")
    pending = chat.propose_change(
        originating_message_id=msg.message_id,
        proposed_change="Pozycja 2: cena 3400 PLN po weryfikacji",
        expected_revision=1,
    )
    approved = chat.approve_change(pending.request_id, expected_revision=1, approved=True)
    assert approved.state == ChangeState.APPROVED
    assert len(chat.approved_for_replan(expected_revision=1)) == 1
    with pytest.raises(ValueError, match="independent_postcondition_required"):
        chat.mark_applied(pending.request_id, expected_revision=1,
                          independently_verified=False)
    assert chat.mark_applied(pending.request_id, expected_revision=1,
                             independently_verified=True).state == ChangeState.APPLIED


def test_rejected_change_is_not_applied():
    chat, _ = setup_chat()
    msg = chat.user_message("Może zmienimy szkło")
    change = chat.propose_change(
        originating_message_id=msg.message_id,
        proposed_change="Pakiet trzyszybowy", expected_revision=1,
    )
    chat.approve_change(change.request_id, expected_revision=1, approved=False)
    assert chat.approved_for_replan(expected_revision=1) == ()
    with pytest.raises(ValueError, match="approved_current_change_required"):
        chat.mark_applied(change.request_id, expected_revision=1,
                          independently_verified=True)


def test_user_writing_again_makes_pending_proposal_stale():
    chat, _ = setup_chat()
    msg = chat.user_message("Wersja A")
    change = chat.propose_change(
        originating_message_id=msg.message_id, proposed_change="Opis A",
        expected_revision=1,
    )
    chat.user_message("Jednak wersja B")
    with pytest.raises(ValueError, match="stale_chat_revision"):
        chat.approve_change(change.request_id, expected_revision=1, approved=True)
    with pytest.raises(ValueError, match="stale_chat_revision"):
        chat.propose_change(originating_message_id=msg.message_id,
                            proposed_change="Opis A", expected_revision=1)


def test_new_message_from_another_document_cannot_be_retargeted():
    chat, _ = setup_chat()
    msg = chat.user_message("Popraw pozycję")
    change = chat.propose_change(
        originating_message_id=msg.message_id, proposed_change="Edytuj 1",
        expected_revision=1,
    )
    assert change.document_key == "OFR/101"


def test_callback_is_used_to_interrupt_shared_host():
    gate = LocalInputArbiter()
    calls = []
    chat = MissionChat(
        document_key="OFR/101", arbiter=gate,
        on_takeover=lambda: (calls.append("takeover"), gate.takeover()),
    )
    chat.user_message("Zatrzymaj i zmień opis")
    assert calls == ["takeover"] and gate.owner == InputOwner.HUMAN


def test_empty_and_oversized_messages_rejected():
    chat, _ = setup_chat()
    for invalid in ("   ", "", "x" * 4001):
        with pytest.raises(ValueError, match="invalid_chat_message"):
            chat.user_message(invalid)
    assert chat.snapshot().mission_revision == 0


def test_fake_agent_response_cannot_change_mission_revision():
    chat, _ = setup_chat()
    chat.user_message("Proszę poprawić opis")
    chat.agent_message("Proponuję poprawkę", based_on_revision=1)
    assert chat.snapshot().mission_revision == 1


def test_unapproved_change_never_marked_as_applied():
    chat, _ = setup_chat()
    msg = chat.user_message("Zmień ilość")
    change = chat.propose_change(
        originating_message_id=msg.message_id,
        proposed_change="Ilość 2", expected_revision=1,
    )
    with pytest.raises(ValueError, match="approved_current_change_required"):
        chat.mark_applied(change.request_id, expected_revision=1,
                          independently_verified=True)


def test_no_model_or_file_access_in_chat():
    chat, _ = setup_chat()
    assert not hasattr(chat, "execute_windows")
    assert not hasattr(chat, "save_offer")
    assert not hasattr(chat, "install_program")
