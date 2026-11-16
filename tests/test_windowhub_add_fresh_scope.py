"""The live Add executor must re-observe before choosing an MDI child."""
from types import SimpleNamespace as NS
from unittest.mock import patch
import pytest

from app.agent.agent_action import AgentAction
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.runtime.windowhub_goal_v2_coordinator import execute_v2_step


def test_add_position_reobserves_current_offer_before_execution():
    original = NS(observation=NS(state=NS(
        active_window_title="Okna - OFR/4678-",
    )))
    refreshed = NS(observation=NS(state=NS(
        active_window_title="Okna - OFR/4680-",
    )))
    target = SemanticTargetQuery(
        role="button", label="Dodaj", uia_runtime_id="rid-A",
    )
    resolved = NS(action=AgentAction(
        name="click_screen_element",
        description="Add a new position",
        target=target,
    ))
    requested = []
    loop = NS(observe_scene=lambda: (requested.append("observed"), refreshed)[1])
    with patch(
        "app.agent.runtime.windowhub_mdi_native_probe.enrich_native_mdi_document_scope",
        side_effect=lambda scene: scene,
    ), patch(
        "app.agent.runtime.windowhub_goal_v2_coordinator.enforce_v2_live_policy",
        side_effect=lambda scene, resolved, approved_persistent=False: (
            requested.append(scene), (_ for _ in ()).throw(ValueError("stale document"))
        )[1],
    ):
        with pytest.raises(ValueError, match="stale document"):
            execute_v2_step(loop, original, resolved)
    assert requested[0] == "observed"
    assert requested[1] is refreshed
