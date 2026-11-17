"""ZLC order documents are classified separately and V2 mutations are blocked."""
from types import SimpleNamespace

import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.windowhub_discovery_diagnostics import categorize_window_title
from app.agent.runtime.windowhub_goal_v2_coordinator import enforce_v2_live_policy


def scene(title):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application="Okna.exe", active_window_title=title)
        ),
        elements=(),
    )


def test_zlc_stage_is_order_not_offer():
    assert stage_of(scene("Okna - ZLC/1312- perfectline <>")) == "order_document"
    assert stage_of(scene("Okna - OFR/4687-")) == "offer_document"


def test_zlc_discovery_category_is_distinct():
    assert categorize_window_title("Okna - ZLC/1312- perfectline <>") == "order_document"


def test_zlc_rejects_v2_action_before_target_resolution():
    fake_resolved = SimpleNamespace(
        action=SimpleNamespace(
            name="click_screen_element", target=None, requires_confirmation=False
        )
    )
    with pytest.raises(ValueError, match="v2_order_document_read_only"):
        enforce_v2_live_policy(
            scene("Okna - ZLC/1312- perfectline <>"), fake_resolved
        )
