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


def test_unique_verified_add_is_explicit_first_step_before_dimensions():
    from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
    from dataclasses import replace
    from app.agent.perception.screen_element import ScreenElement
    from app.agent.perception.interaction_capability import InteractionCapability

    # An OFR Add capability is deliberately absent unless the scene also
    # proves exactly one selected document tab and the button's MDI owner.
    # Test the real security prerequisite instead of mocking an unsafe click.
    active_offer = "OFR/4488-4300 <>"
    original = synthetic_scene("Okna - " + active_offer, label="Dodaj")
    add_button = replace(
        original.elements[0],
        metadata={
            **original.elements[0].metadata,
            "document_scope": active_offer,
            "document_scope_source": "verified_native_mdi_child",
        },
    )
    tab = ScreenElement(
        kind="tabitem", label=active_offer,
        x=200, y=20, width=140, height=30,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "uia_control_type": "tabitem",
            "uia_visible": True,
            "uia_enabled": True,
            "uia_selected": True,
            "uia_tab_scope": "document",
            "uia_runtime_id": "[synthetic-active-offer-tab]",
            "automation_id": "synthetic_tab",
        },
    )
    scene = replace(original, elements=(add_button, tab))
    request = ComputerUseV2ActionSession().prepare_cycle(
        scene,
        task_id="offer-step-order", goal="Dodaj okno 1500x1400",
        world_revision=1, observed_at="2026-11-17T09:00:00Z",
    ).request_payload
    cap = next(
        c for c in request["capabilities"]["actions"]
        if c["name"].startswith("click_ent_")
    )
    request["metadata"]["verified_windowhub_stage"] = "offer_document"
    request["metadata"]["verified_active_offer_add_refs"] = [cap["target_ref"]]
    view = compact_local_model_view(request)
    assert view["stage"] == "offer_document"
    assert len(view["actions"]) == 1
    assert view["actions"][0]["target_ref"] == cap["target_ref"]
    assert "FIRST" not in view["current_step"]
    assert "after the dimensions wizard" in view["current_step"]
    assert "Dodaj" in view["current_step"]
