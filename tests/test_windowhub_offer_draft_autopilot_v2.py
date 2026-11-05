"""Stage policy tests for the bounded offer-draft autopilot."""
import pytest
from tools.run_windowhub_offer_draft_autopilot_v2 import permitted_label, pick_action, resolve_verified_navigation


@pytest.mark.parametrize("stage,label,allowed", [
    ("start", "NOWA OFERTA", True),
    ("offer_document", "NOWA OFERTA", True),
    ("offer_document", "Dodaj", False),
    ("offer_document", "WYSLIJ LUB ODBIERZ ZLECENIE", False),
    ("document_properties", "Wybierz istniejącego klienta", True),
    ("document_properties", "OK", False),
    ("document_properties", "Zapisz", False),
    ("windowhub_unmapped", "Customer A", True),
    ("windowhub_unmapped", "Customer B", False),
    ("windowhub_unmapped", "OK", False),
])
def test_only_navigation_and_exact_customer_are_allowed(stage, label, allowed):
    assert permitted_label(stage, label, customer="Customer A") is allowed


def test_customer_is_never_guessed():
    assert not permitted_label("windowhub_unmapped", "Customer A", customer="")
    assert not permitted_label("document_properties", "OK", customer="")


def test_model_cannot_confirm_or_send_in_document_properties():
    class Prepared:
        request_payload = {
            "capabilities": {
                "actions": [
                    {"name": "click_ent_0001", "target_ref": "ent_0001", "requires_confirmation": True},
                ],
            },
            "world": {
                "entities": [
                    {"ref": "ent_0001", "label": "OK"},
                ],
            },
        }
    response = {
        "decision": "act",
        "confidence": 1.0,
        "action": {
            "name": "click_ent_0001",
            "target_ref": "ent_0001",
            "requires_confirmation": True,
        },
    }
    with pytest.raises(ValueError, match="action_not_allowed_in_stage"):
        pick_action(Prepared(), response, "document_properties", customer="Customer A")


def test_local_navigation_uses_single_validated_capability():
    from types import SimpleNamespace
    cap = {
        "name": "click_ent_0001",
        "target_ref": "ent_0001",
        "requires_confirmation": False,
    }
    captured = []
    class Prepared:
        request_payload = {"task_id": "test-offer"}
        def resolve_action_decision(self, response):
            captured.append(response)
            return SimpleNamespace(action=SimpleNamespace(name="click_screen_element"))

    result = resolve_verified_navigation(Prepared(), cap)
    assert result.action.name == "click_screen_element"
    assert captured[0]["decision"] == "act"
    assert captured[0]["action"]["target_ref"] == "ent_0001"
    assert captured[0]["action"]["expected_postcondition"] == {"kind": "scene_changed"}
    assert captured[0]["action"]["requires_confirmation"] is False


def test_local_navigation_refuses_confirmation_required_capability():
    cap = {
        "name": "click_ent_0001",
        "target_ref": "ent_0001",
        "requires_confirmation": True,
    }
    with pytest.raises(ValueError, match="navigation_requires_confirmation"):
        resolve_verified_navigation(None, cap)
