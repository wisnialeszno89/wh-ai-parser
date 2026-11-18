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
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: SimpleNamespace(**vars(s)))
    monkeypatch.setattr(first, "unique_active_document_control",
                        lambda s, label: element())
    observed, decision, offer = first.prepare_add_action(scene())
    assert offer == "OFR/4708-"
    assert decision.action.target.label == "Dodaj"
    assert decision.action.target.uia_runtime_id == "rid-1"
    assert decision.expected_postcondition == {"kind": "scene_changed"}
    assert decision.action.requires_environment_observation


def test_refuses_order_document(monkeypatch):
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: SimpleNamespace(**vars(s)))
    with pytest.raises(ValueError, match="test_offer_document_required"):
        first.prepare_add_action(scene("Okna - ZLC/4708-"))


def test_unverified_dodaj_fails_closed(monkeypatch):
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: SimpleNamespace(**vars(s)))
    monkeypatch.setattr(first, "unique_active_document_control",
                        lambda s, label: None)
    with pytest.raises(ValueError, match="unique_active_dodaj_not_verified"):
        first.prepare_add_action(scene())


def test_missing_runtime_identity_rejected(monkeypatch):
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: SimpleNamespace(**vars(s)))
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
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: SimpleNamespace(**vars(s)))
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


def test_live_requires_explicit_test_offer_before_observing(monkeypatch, capsys):
    monkeypatch.setattr(first, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(first.sys, "argv", ["whokna", "--execute-live"])
    assert first.main() == 2
    assert "WH_STEP_STOP=explicit_test_offer_required" in capsys.readouterr().out


def test_cached_document_scope_is_not_accepted_without_fresh_proof(monkeypatch):
    monkeypatch.setattr(first, "enrich_native_mdi_document_scope", lambda s: s)
    monkeypatch.setattr(first, "unique_active_document_control", lambda s, label: element())
    with pytest.raises(ValueError, match="unique_active_dodaj_not_verified"):
        first.prepare_add_action(scene())


@pytest.mark.parametrize("tab, title, expected", [
    ("OFR/42-", "Okna - OFR/42 <>", True),
    ("OFR/42", "Okna - OFR/42-99 <>", False),
    ("OFR/42-99", "Okna - OFR/42-99 <>", False),
    ("OFR/43-", "Okna - OFR/42 <>", False),
    ("OFR/42-", "Okna - OFR/42 customer text", False),
])
def test_cli_requires_requested_full_id_in_both_tab_and_foreground(
    monkeypatch, capsys, tab, title, expected,
):
    observed = scene(title)
    observed.elements = (SimpleNamespace(kind="tabitem", label=tab, metadata={
        "source": "windows_ui_automation", "uia_tab_scope": "document",
        "uia_visible": True, "uia_selected": True,
    }),)
    monkeypatch.setattr(first, "os", SimpleNamespace(
        name="nt", environ={"COMPUTER_USE_LIVE": "1", "WH_REAL_WINDOWHUB": "1"},
    ))
    monkeypatch.setattr(first.sys, "argv", [
        "whokna", "--offer", "OFR/42-", "--execute-live", "--start-delay", "0",
    ])
    monkeypatch.setattr(first, "create_windows_desktop_agent_control_loop", object)
    monkeypatch.setattr(first, "observe_offer_gate", lambda loop: (
        SimpleNamespace(ok=True, scene_stage="offer_document"), observed,
    ))
    monkeypatch.setattr(first, "prepare_add_action", lambda s: (s, None, title[7:]))
    calls = []
    monkeypatch.setattr(first, "execute_v2_step", lambda *args, **kwargs: calls.append(kwargs))
    assert first.main() == (0 if expected else 4)
    assert calls == ([{"expected_offer": title[7:], "approved_persistent": False}] if expected else [])
    output = capsys.readouterr().out
    assert "WH_STEP_OFFER_IDENTITY=" in output
    assert "OFR/" not in output
    assert "customer text" not in output


def test_inspect_current_reports_wizard_without_preparing_or_executing(monkeypatch, capsys):
    observed = scene("Dodawanie nowej pozycji")
    monkeypatch.setattr(first, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(first.sys, "argv", ["whokna", "--inspect-current", "--start-delay", "0"])
    monkeypatch.setattr(first, "create_windows_desktop_agent_control_loop", lambda: SimpleNamespace(
        observe_scene=lambda: observed,
    ))
    assert first.main() == 0
    output = capsys.readouterr().out
    assert '"wizard_step": "position"' in output
    assert '"exact_position_title": true' in output
    assert "WH_STEP_ACTIONS_EXECUTED=0" in output


def test_current_state_diagnostic_redacts_unknown_window_title():
    diagnostic = first.windowhub_add_postcondition_diagnostic(scene("Private customer details"))
    assert diagnostic["foreground_kind"] == "unrecognized"
    assert diagnostic["wizard_step"] is None
    assert "Private customer details" not in str(diagnostic)


def test_current_state_distinguishes_same_offer_from_a_different_foreground():
    diagnostic = first.windowhub_add_postcondition_diagnostic(
        scene("Okna - OFR/4708 <>"), "OFR/4708-",
    )
    assert diagnostic["requested_offer_still_foreground"] is True
    assert "4708" not in str(diagnostic)
