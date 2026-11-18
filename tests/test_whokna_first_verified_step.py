"""One-step WindowHub handoff contract; no real desktop actions."""
from types import SimpleNamespace

import pytest

from tools import run_navimind_whokna_first_verified_step as first


def scene(title="Okna - OFR/4708-"):
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(
                active_window_title=title, active_application="Okna.exe"
            ),
            metadata={},
        ),
        elements=(),
    )


def element():
    return SimpleNamespace(
        metadata={"uia_runtime_id": "rid-1", "automation_id": "button-1"}
    )


def test_dodaj_handoff_is_semantic_and_verified(monkeypatch):
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: s)
    monkeypatch.setattr(first, "unique_active_document_control",
                        lambda s, label: element())
    observed, decision, offer = first.prepare_add_action(scene())
    assert offer == "OFR/4708-"
    assert decision.action.target.label == "Dodaj"
    assert decision.action.target.uia_runtime_id == "rid-1"
    assert decision.expected_postcondition == {"kind": "scene_changed"}
    assert decision.action.requires_environment_observation


def test_refuses_order_document(monkeypatch):
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: s)
    with pytest.raises(ValueError, match="test_offer_document_required"):
        first.prepare_add_action(scene("Okna - ZLC/4708-"))


def test_unverified_dodaj_fails_closed(monkeypatch):
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: s)
    monkeypatch.setattr(first, "unique_active_document_control",
                        lambda s, label: None)
    with pytest.raises(ValueError, match="unique_active_dodaj_not_verified"):
        first.prepare_add_action(scene())


def test_missing_runtime_identity_rejected(monkeypatch):
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: s)
    monkeypatch.setattr(first, "unique_active_document_control",
                        lambda s, label: SimpleNamespace(metadata={}))
    with pytest.raises(ValueError, match="runtime_id_missing"):
        first.prepare_add_action(scene())


def test_unverified_target_diagnostic_is_read_only(monkeypatch):
    monkeypatch.setattr(first, "duplicate_document_action_status",
                        lambda s, label: {
                            "selected_document_status": "no_unique_selected_document_tab",
                            "observed": 2, "active_scope_proven": 0,
                            "unresolved_scope": 2,
                            "safe_unique_active_target": False,
                        })
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: s)
    monkeypatch.setattr(first, "inspect_native_mdi_button_ancestry",
                        lambda s: {
                            "status": "diagnostic_only_no_native_authorization",
                            "uia_matched_uniquely": 2,
                            "with_exact_mdi_ancestor": 0,
                            "with_no_mdi_ancestor": 2,
                            "with_ambiguous_mdi_ancestor": 0,
                        })
    result = first.diagnose_add_scope(scene())
    assert result["observed_dodaj"] == 2
    assert result["safe_unique_target"] is False
    assert result["native_without_mdi_ancestor"] == 2
    assert "document" not in result


def test_foreground_failure_report_redacts_window_title():
    gate = SimpleNamespace(
        reason="unrecognized_windowhub_stage",
        scene_stage="unknown",
    )
    s = scene("Private Client Account 1234")
    diagnostic = first.stopped_foreground_diagnostic(gate, s)
    assert diagnostic["gate_reason"] == "unrecognized_windowhub_stage"
    assert diagnostic["scene_elements"] == 0
    assert diagnostic["window_rect_type"] == "missing"
    assert "Private Client" not in str(diagnostic)
    assert diagnostic["is_windowhub_process"] is True
