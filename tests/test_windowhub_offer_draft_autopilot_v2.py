"""Stage policy tests for the bounded offer-draft autopilot."""
import pytest
from tools.run_windowhub_offer_draft_autopilot_v2 import permitted_label, pick_action, resolve_verified_navigation, stage_transition_verified


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


@pytest.mark.parametrize("before,after,expected", [
    ("offer_document", "document_properties", True),
    ("start", "document_properties", True),
    ("offer_document", "offer_document", False),
    ("offer_document", "start", False),
    ("offer_document", "windowhub_unmapped", False),
    ("document_properties", "offer_document", False),
    ("document_properties", "windowhub_unmapped", True),
    ("document_properties", "customer_lookup", True),
    ("document_properties", "document_properties", False),
])
def test_navigation_requires_expected_destination(before, after, expected):
    assert stage_transition_verified(before, after) is expected


def test_native_navigation_uses_proven_invoke_without_mouse_or_model(monkeypatch):
    from tools import run_windowhub_offer_draft_autopilot_v2 as workflow
    from types import SimpleNamespace
    calls = []
    class Invoke:
        def Invoke(self):
            calls.append("invoke")
    def fake_resolve(scene, **kwargs):
        calls.append(kwargs)
        return Invoke()
    monkeypatch.setattr(workflow, "resolve_native_control", fake_resolve)
    label = workflow.invoke_known_navigation(SimpleNamespace(), "offer_document")
    assert label == "NOWA OFERTA"
    assert calls[0]["allowed_stages"] == ("offer_document",)
    assert calls[0]["label"] == "NOWA OFERTA"
    assert calls[1] == "invoke"


def test_customer_picker_uses_unique_native_wrapper_click_without_invoke(monkeypatch):
    from tools import run_windowhub_offer_draft_autopilot_v2 as workflow
    from types import SimpleNamespace
    calls = []
    def fake_resolve(scene, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(click_input=lambda: calls.append("click_input"))
    monkeypatch.setattr(workflow, "resolve_native_wrapper", fake_resolve)
    monkeypatch.setattr(workflow, "resolve_native_control", lambda *args, **kwargs: pytest.fail("no invoke for customer picker"))
    workflow.invoke_known_navigation(SimpleNamespace(), "document_properties")
    assert calls[0]["automation_id"] == "IDC_ZAMAWIAJACY"
    assert calls[0]["allowed_stages"] == ("document_properties",)
    assert calls == [calls[0], "click_input"]


def test_unknown_stage_never_uses_native_navigation():
    from tools.run_windowhub_offer_draft_autopilot_v2 import invoke_known_navigation
    with pytest.raises(KeyError):
        invoke_known_navigation(None, "windowhub_unmapped")


def test_picker_transition_requires_new_foreground_window(monkeypatch):
    from tools import run_windowhub_offer_draft_autopilot_v2 as workflow
    from types import SimpleNamespace

    def scene_for(hwnd):
        return SimpleNamespace(
            observation=SimpleNamespace(metadata={"window_handle": hwnd})
        )

    class Loop:
        def __init__(self, hwnd):
            self.hwnd = hwnd
        def observe_scene(self):
            return scene_for(self.hwnd)

    monkeypatch.setattr(workflow, "enrich_windowhub_scene", lambda scene: scene)
    monkeypatch.setattr(workflow, "stage_of", lambda scene: "windowhub_unmapped")
    same, _ = workflow.observe_transition(
        Loop(100), "document_properties", attempts=1, previous_window_handle=100
    )
    new, _ = workflow.observe_transition(
        Loop(101), "document_properties", attempts=1, previous_window_handle=100
    )
    assert same is False
    assert new is True
