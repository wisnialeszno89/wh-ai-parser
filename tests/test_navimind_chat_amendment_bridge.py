"""Contract tests for conversational revisions and human approval."""
import pytest

from app.agent.runtime.navimind_local_input_arbiter import LocalInputArbiter
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_chat_amendment_bridge import (
    Field, PositionEvidence, ProposalState, parse_bounded_instruction,
    prepare_amendment, approved_amendment,
)
from app.agent.offers.navimind_quote_revision_planner import RevisionRoute


def chat():
    return MissionChat(document_key="OFR/101", arbiter=LocalInputArbiter())


def evidence(**kwargs):
    args = dict(
        document_key="OFR/101", position_id="3",
        fields={
            "colour": "biały", "width_mm": "1200",
            "height_mm": "1400", "quantity": "1",
        },
        exact_document_verified=True, exact_position_verified=True,
        fresh=True,
        editable_fields=("colour", "width_mm", "height_mm", "quantity"),
    )
    args.update(kwargs)
    return PositionEvidence(**args)


@pytest.mark.parametrize("message,field,value", [
    ("Zmień kolor w pozycji 3 na antracyt", Field.COLOUR, "antracyt"),
    ("Ustaw szerokość w poz. 3 na 1500 mm", Field.WIDTH_MM, "1500"),
    ("Zmien wysokość w pozycji 3 na 1800 mm", Field.HEIGHT_MM, "1800"),
    ("Zmień ilość w pozycji 3 na 2 szt.", Field.QUANTITY, "2"),
])
def test_recognizes_single_supported_position_change(message, field, value):
    parsed, reason = parse_bounded_instruction(message)
    assert reason == "recognized"
    assert parsed.position_id == "3"
    assert parsed.field == field
    assert parsed.value == value


@pytest.mark.parametrize("message", [
    "Zmień kolor na antracyt",
    "Zmień kolor w pozycji 3 i 4 na antracyt",
    "Nie zmieniaj koloru w pozycji 3 na antracyt",
    "Zmień kolor w pozycji 3 na antracyt i ustaw szerokość na 1500",
    "Ustaw szerokość w pozycji 3 na 999999 mm",
    "Ustaw cenę w pozycji 3 na 180 PLN",
    "Zapisz ofertę",
    "Zmień klienta na innego",
    "Wstaw zdjęcie panelu",
    "",
])
def test_unsupported_or_ambiguous_instructions_are_not_parsed(message):
    parsed, reason = parse_bounded_instruction(message)
    assert parsed is None
    assert reason != "recognized"


def test_verified_colour_change_creates_one_review_request_not_action():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposed = prepare_amendment(c, message_id=msg.message_id, evidence=evidence())
    assert proposed.state == ProposalState.READY_FOR_REVIEW
    assert proposed.amendment.value == "antracyt"
    assert proposed.quote_plan.route == RevisionRoute.EDIT_EXISTING
    assert proposed.request_id == 1
    assert not proposed.native_action_executed
    assert not proposed.customer_quote_saved
    with pytest.raises(ValueError, match="explicit_salesperson_approval_required"):
        approved_amendment(c, proposed)


def test_approval_releases_structured_data_but_never_executes():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(c, message_id=msg.message_id, evidence=evidence())
    c.approve_change(proposal.request_id, expected_revision=msg.mission_revision,
                     approved=True)
    approved = approved_amendment(c, proposal)
    assert approved.position_id == "3"
    assert approved.field == Field.COLOUR
    assert approved.value == "antracyt"
    assert not proposal.native_action_executed
    assert not proposal.customer_quote_saved


def test_explicit_rejection_never_releases_an_action():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(c, message_id=msg.message_id, evidence=evidence())
    c.approve_change(proposal.request_id, expected_revision=1, approved=False)
    with pytest.raises(ValueError, match="explicit_salesperson_approval_required"):
        approved_amendment(c, proposal)


def test_new_chat_instruction_invalidates_old_approved_proposal():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(c, message_id=msg.message_id, evidence=evidence())
    c.approve_change(proposal.request_id, expected_revision=1, approved=True)
    c.user_message("Jednak pozostaw biały")
    with pytest.raises(ValueError, match="stale_or_wrong_document_proposal"):
        approved_amendment(c, proposal)


def test_exact_offer_identity_is_mandatory():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(
        c, message_id=msg.message_id,
        evidence=evidence(document_key="OFR/OTHER"),
    )
    assert proposal.state == ProposalState.NEEDS_REVIEW
    assert proposal.request_id is None


def test_exact_position_identity_is_mandatory():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(
        c, message_id=msg.message_id, evidence=evidence(position_id="2"),
    )
    assert proposal.state == ProposalState.NEEDS_REVIEW


def test_fresh_readback_is_mandatory():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(
        c, message_id=msg.message_id, evidence=evidence(fresh=False),
    )
    assert proposal.state == ProposalState.NEEDS_REVIEW


def test_editing_field_without_verified_ui_capability_is_not_allowed():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(
        c, message_id=msg.message_id,
        evidence=evidence(editable_fields=("width_mm",)),
    )
    assert proposal.state == ProposalState.NEEDS_REVIEW
    assert proposal.reason == "field_edit_not_proven_supported"


def test_existing_value_already_matches_without_duplicate_edit():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(
        c, message_id=msg.message_id,
        evidence=evidence(fields={"colour": "antracyt"}),
    )
    assert proposal.state == ProposalState.NEEDS_REVIEW
    assert proposal.reason == "no_effective_change"


def test_missing_current_value_is_not_guessed():
    c = chat()
    msg = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = prepare_amendment(
        c, message_id=msg.message_id,
        evidence=evidence(fields={}),
    )
    assert proposal.reason == "existing_field_value_not_verified"


def test_unsupported_price_change_never_uses_component_price():
    c = chat()
    msg = c.user_message("Ustaw cenę w pozycji 3 na 850 zł")
    proposal = prepare_amendment(c, message_id=msg.message_id, evidence=evidence())
    assert proposal.state == ProposalState.NEEDS_REVIEW
    assert proposal.request_id is None


def test_older_chat_message_cannot_create_new_plan():
    c = chat()
    m = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    c.user_message("Nie, zrób inaczej")
    with pytest.raises(ValueError, match="current_human_instruction_required"):
        prepare_amendment(c, message_id=m.message_id, evidence=evidence())


def test_chat_reply_from_model_is_not_a_human_order():
    c = chat()
    c.user_message("Witam")
    reply = c.agent_message("Zmień kolor w pozycji 3 na antracyt", based_on_revision=1)
    with pytest.raises(ValueError, match="current_human_instruction_required"):
        prepare_amendment(c, message_id=reply.message_id, evidence=evidence())


def test_combined_save_and_colour_instruction_is_not_partially_executed():
    c = chat()
    m = c.user_message("Zmień kolor w pozycji 3 na antracyt i zapisz ofertę")
    p = prepare_amendment(c, message_id=m.message_id, evidence=evidence())
    assert p.state == ProposalState.NEEDS_REVIEW
    assert p.request_id is None


def test_cannot_forge_approved_amendment_value_even_with_same_request_id():
    from dataclasses import replace
    c = chat()
    m = c.user_message("Zmień kolor w pozycji 3 na antracyt")
    p = prepare_amendment(c, message_id=m.message_id, evidence=evidence())
    c.approve_change(p.request_id, expected_revision=1, approved=True)
    forged = replace(p, amendment=replace(p.amendment, value="czarny"))
    with pytest.raises(ValueError, match="proposal_binding_invalid"):
        approved_amendment(c, forged)


def test_shared_host_stages_only_independently_verified_position_evidence():
    from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost
    host = NaviMindSharedHost("OFR/101")
    m = host.chat.user_message("Zmień kolor w pozycji 3 na antracyt")
    proposal = host.propose_amendment_from_chat(
        human_message_id=m.message_id, position_evidence=evidence()
    )
    assert proposal.state == ProposalState.READY_FOR_REVIEW
    assert host.controller.snapshot().human_controls
    assert host.controller.current_permit() is None


def test_stopped_host_cannot_stage_new_change():
    from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost
    host = NaviMindSharedHost("OFR/101")
    m = host.chat.user_message("Zmień kolor w pozycji 3 na antracyt")
    host.stop()
    with pytest.raises(ValueError, match="stopped_mission"):
        host.propose_amendment_from_chat(
            human_message_id=m.message_id, position_evidence=evidence()
        )
