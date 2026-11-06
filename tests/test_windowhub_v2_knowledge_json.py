"""Regression: curated WindowHub construction knowledge must satisfy strict V2 JSON."""
import json

from app.agent.learning.windowhub_training_context import (
    windowhub_skill_knowledge, _json_compatible_construction_map,
)
from app.agent.learning.windowhub_construction_learning import construction_map_coverage
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from app.agent.bridge.agent_task_contract_v2 import validate_agent_task_v2_payload
from tools.smoke_navimind_v2_offline import synthetic_scene


def test_windowhub_skill_knowledge_serializes_as_strict_json():
    knowledge = windowhub_skill_knowledge()
    encoded = json.dumps(knowledge, ensure_ascii=False, allow_nan=False)
    decoded = json.loads(encoded)
    assert isinstance(decoded["construction_ui_mapping"]
                      ["mapped_groups"]["item_type"]["mapped_fields"], list)
    assert isinstance(decoded["construction_ui_mapping"]
                      ["pending_groups"], list)
    assert "ui_mapping" not in decoded["window_construction_learning"]


def test_full_windowhub_v2_cycle_accepts_construction_knowledge():
    scene = synthetic_scene("Okna - Start1")
    cycle = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id="knowledge-regression", goal="Create WindowHub offer",
        world_revision=1, knowledge=windowhub_skill_knowledge(),
        observed_at="2026-11-06T08:45:00Z",
    )
    validate_agent_task_v2_payload(cycle.request_payload)


def test_mapping_report_remains_immutable_for_existing_local_consumers():
    mapping = construction_map_coverage()
    assert isinstance(mapping["mapped_groups"]["item_type"]["mapped_fields"], tuple)
    converted = _json_compatible_construction_map(mapping)
    assert isinstance(converted["mapped_groups"]["item_type"]["mapped_fields"], list)
    assert isinstance(mapping["mapped_groups"]["item_type"]["mapped_fields"], tuple)


def test_unsupported_mapping_values_fail_closed():
    import pytest
    with pytest.raises(TypeError, match="unsupported_type"):
        _json_compatible_construction_map({"invalid": object()})
