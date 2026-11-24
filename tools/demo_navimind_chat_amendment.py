"""Portable demo: conversational colour correction -> review -> approval.

The evidence is entirely synthetic; WindowHub is never opened or modified.
The existing mission chat remains human-owned after a user instruction.
"""
from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.navimind_chat_amendment_bridge import (
    PositionEvidence, ProposalState, approved_amendment,
)
from app.agent.runtime.navimind_shared_control_host import NaviMindSharedHost


def main() -> int:
    host = NaviMindSharedHost("OFR/101")
    msg = host.chat.user_message("Zmień kolor w pozycji 3 na antracyt")
    evidence = PositionEvidence(
        document_key="OFR/101",
        position_id="3",
        fields={"colour": "biały", "width_mm": "1500"},
        exact_document_verified=True,
        exact_position_verified=True,
        fresh=True,
        editable_fields=("colour",),
    )
    proposal = host.propose_amendment_from_chat(
        human_message_id=msg.message_id, position_evidence=evidence,
    )
    print("HUMAN_INSTRUCTION_ACCEPTED=" + str(msg.message_id == 1))
    print("STRUCTURED_CHANGE_FOUND=" + str(
        proposal.state == ProposalState.READY_FOR_REVIEW
    ))
    print("POSITION_ID=" + str(proposal.amendment.position_id))
    print("CHANGED_FIELD=" + proposal.amendment.field.value)
    print("NEW_VALUE=" + proposal.amendment.value)
    print("AMEND_ROUTE=" + proposal.quote_plan.route.value)
    print("CHANGE_APPROVED_BEFORE_REVIEW=False")
    host.chat.approve_change(
        proposal.request_id, expected_revision=msg.mission_revision,
        approved=True,
    )
    approved = approved_amendment(host.chat, proposal)
    print("CHANGE_APPROVED_AFTER_REVIEW=" + str(approved == proposal.amendment))
    print("USER_STILL_CONTROLS_DESKTOP=" + str(
        host.controller.snapshot().human_controls
    ))
    print("AUTOMATIC_GUI_ACTIONS=0")
    print("OFFER_SAVED=False")
    print("REAL_WINDOWHUB_CONNECTED=False")
    return 0 if (
        approved == proposal.amendment
        and host.controller.snapshot().human_controls
        and not proposal.native_action_executed
        and not proposal.customer_quote_saved
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
