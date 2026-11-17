"""Offer-stage model proposals must be MDI-scoped; never open NEW OFFER by accident."""
from app.agent.reasoning.local_ollama_task_reasoner_v2 import (
    compact_local_model_view, LocalOllamaTaskReasonerV2,
)
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from tools.smoke_navimind_v2_offline import synthetic_scene


def request_for_offer():
    scene = synthetic_scene("Okna - OFR/4488-4300 <>", label="NOWA OFERTA")
    prepared = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id="offer-safety", goal="Dodaj pozycje do istniejącej oferty",
        world_revision=1, observed_at="2026-11-17T09:00:00Z",
    )
    return prepared.request_payload


def test_unscoped_offer_has_no_model_actions():
    request = request_for_offer()
    view = compact_local_model_view(request)
    assert view["stage"] == "offer_document"
    assert view["actions"] == []


def test_unscoped_offer_returns_manual_review_without_ai_call():
    request = request_for_offer()
    def forbidden_opener(*args, **kwargs):
        raise AssertionError("must not call Ollama for unscoped offer")
    reasoner = LocalOllamaTaskReasonerV2(opener=forbidden_opener)
    reply = reasoner.reason(request)
    assert reply["decision"] == "manual_review"
    assert reply["requires_manual_review"] is True
    assert reply["action"] is None


def test_fake_new_offer_cannot_become_active_offer_add():
    request = request_for_offer()
    cap = next(a for a in request["capabilities"]["actions"] if a["name"].startswith("click_ent_"))
    request["metadata"]["verified_active_offer_add_refs"] = [cap["target_ref"]]
    # Native proof alone must not launder a control whose semantic label is wrong.
    assert compact_local_model_view(request)["actions"] == []


def test_verified_offer_stage_overrides_redacted_world_title():
    request = request_for_offer()
    request["world"]["window_title"] = "WindowHub"  # Privacy projection.
    request["metadata"]["verified_windowhub_stage"] = "offer_document"
    view = compact_local_model_view(request)
    assert view["stage"] == "offer_document"
    assert view["actions"] == []


def test_unknown_projected_stage_cannot_offer_random_clicks():
    request = request_for_offer()
    request["world"]["window_title"] = "WindowHub"
    view = compact_local_model_view(request)
    assert view["stage"] == "windowhub_unmapped"
    assert view["actions"] == []
