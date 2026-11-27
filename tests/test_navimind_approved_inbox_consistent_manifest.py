"""The approved-inbox summary and the V2 position ledger share one parser."""
from pathlib import Path

from app.agent.runtime.navimind_enquiry_inbox import LocalEnquiryInbox
from app.agent.runtime.navimind_enquiry_evidence_bridge import (
    summarize_full_approved_inbox,
)
from app.agent.runtime.navimind_position_ledger import build_position_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_two_window_smoke_numbered_positions_in_local_summary():
    text = (ROOT / "examples/navimind_two_window_smoke.txt").read_text(
        encoding="utf-8"
    )
    inbox = LocalEnquiryInbox()
    inbox.set_text(text)
    manifest = build_position_manifest(inbox)
    assert len(manifest.positions) == 2
    summary = summarize_full_approved_inbox(inbox, approved=True)
    assert "WYKRYTE_POZYCJE=2" in summary
    assert "S01-P001" in summary and "S01-P002" in summary
    assert "1500x1400 mm" in summary
    assert "1300x1200 mm" in summary
    assert "Perfectline" in summary
    assert "activPilot" in summary
    assert "Anthrazit" in summary
    assert "Weiss" in summary
    assert "Nie wykonano operacji w WindowHub" in summary


def test_no_document_information_without_user_consent():
    inbox = LocalEnquiryInbox()
    inbox.set_text("1 Stk Fenster 1500x1400 PRIVATE-CUSTOMER")
    result = summarize_full_approved_inbox(inbox, approved=False)
    assert "Brak zgody" in result
    assert "1500" not in result
    assert "PRIVATE" not in result


def test_unparsed_source_is_not_claimed_as_verified():
    inbox = LocalEnquiryInbox()
    inbox.set_text("Witam, nie podano jeszcze wymiarów.")
    result = summarize_full_approved_inbox(inbox, approved=True)
    assert "WYKRYTE_POZYCJE=0" in result
    assert "BLOKADY:" in result
    assert "Parser nie potwierdził pozycji" in result
