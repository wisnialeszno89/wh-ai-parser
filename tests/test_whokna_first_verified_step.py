"""One-step WindowHub handoff contract; no real desktop actions."""
from types import SimpleNamespace

import pytest

from tools import run_navimind_whokna_first_verified_step as first


def scene(title="Okna - OFR/4708-"):
    return SimpleNamespace(
        observation=SimpleNamespace(state=SimpleNamespace(
            active_window_title=title, active_application="Okna.exe"
        ))
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
