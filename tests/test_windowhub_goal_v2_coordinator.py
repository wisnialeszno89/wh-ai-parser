from types import SimpleNamespace
import pytest

from app.agent.agent_action import AgentAction
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.runtime.windowhub_goal_v2_coordinator import (
    verified_v2_outcome, enforce_v2_live_policy,
)


def scene(*elements):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe",
                active_window_title="Właściwości dokumentu",
            ),
        ),
        elements=tuple(elements),
    )


def target(label="OknaWPF"):
    return SemanticTargetQuery(
        role="button", label=label,
        automation_id="IDC_NEW", uia_runtime_id="fresh-runtime",
    )


def button(semantic=True):
    return ScreenElement(
        kind="button", label="OknaWPF",
        metadata={
            "source": "windowhub_ui_automation", "uia_control_type": "button",
            "automation_id": "IDC_NEW", "uia_runtime_id": "fresh-runtime",
            "uia_visible": True, "uia_enabled": True,
            **({"semantic_label": "Dodaj nowego klienta"} if semantic else {}),
        },
    )


def resolved(*, confirmation=False, post=None):
    return SimpleNamespace(
        action=AgentAction(
            name="click_screen_element", target=target(),
            requires_confirmation=confirmation,
        ),
        target_ref="ent_0001",
        expected_postcondition=post or {"kind": "scene_changed"},
    )


def test_intent_action_requires_verified_effect():
    outcome = verified_v2_outcome(resolved())
    assert outcome.require_scene_change is True
    with pytest.raises(ValueError, match="not_strong_enough"):
        verified_v2_outcome(resolved(post={
            "kind": "entity_present", "target_ref": "ent_0001",
        }))


def test_only_approved_meaningful_and_unique_target_can_execute():
    enforce_v2_live_policy(scene(button()), resolved())
    with pytest.raises(ValueError, match="meaning_unknown"):
        enforce_v2_live_policy(scene(button(False)), resolved())
    with pytest.raises(ValueError, match="no_longer_uniquely_observed"):
        enforce_v2_live_policy(scene(button(), button()), resolved())


def test_persisting_customer_requires_operator_approval():
    with pytest.raises(ValueError, match="operator_approval"):
        enforce_v2_live_policy(scene(button()), resolved(confirmation=True))
    enforce_v2_live_policy(
        scene(button()), resolved(confirmation=True),
        approved_persistent=True,
    )


def test_write_requires_same_expected_text_as_action():
    action = AgentAction(
        name="write_text", target=SemanticTargetQuery(
            role="edit", label="Firma", automation_id="FIRMA", uia_runtime_id="text1",
        ), value="XYZ",
    )
    verified = SimpleNamespace(
        action=action, target_ref="ent_0001",
        expected_postcondition={
            "kind": "entity_value_equals",
            "target_ref": "ent_0001",
            "expected_value": "XYZ",
        },
    )
    outcome = verified_v2_outcome(verified)
    assert outcome.expected_element_current_value == "XYZ"
    verified.expected_postcondition["expected_value"] = "WRONG"
    with pytest.raises(ValueError, match="value_mismatch"):
        verified_v2_outcome(verified)
