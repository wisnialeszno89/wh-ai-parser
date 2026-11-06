"""Demonstration learning must distinguish mapped fields without raw values."""
from app.agent.learning.windowhub_demonstration import semantic_transition
from app.agent.learning.windowhub_construction_learning import construction_demonstration_report


def test_dimension_state_change_identifies_unique_width_slot():
    before = {"stage": "dimensions", "controls": {
        "edit:1000": {"role": "edit", "label": "Szerokość",
                      "state": {"value_present": False}},
    }}
    after = {"stage": "dimensions", "controls": {
        "edit:1000": {"role": "edit", "label": "Szerokość",
                      "state": {"value_present": True}},
    }}
    result = semantic_transition(before, after)
    change = result["changed"][0]
    assert change["field_name"] == "width_1"
    assert "1000" not in change.values()
    report = construction_demonstration_report([{
        "type": "transition", "transition": result,
    }])
    assert "width_1" in report["construction_groups"]["dimensions"]["fields_with_observed_effect"]


def test_ambiguous_or_unmapped_field_does_not_learn_identity():
    before = {"stage": "dimensions", "controls": {
        "edit:999999": {"role": "edit", "label": "Szerokość",
                        "state": {"value_present": False}},
    }}
    after = {"stage": "dimensions", "controls": {
        "edit:999999": {"role": "edit", "label": "Szerokość",
                        "state": {"value_present": True}},
    }}
    result = semantic_transition(before, after)
    assert "field_name" not in result["changed"][0]
    report = construction_demonstration_report([{
        "type": "transition", "transition": result,
    }])
    assert report["construction_groups"]["dimensions"]["fields_with_observed_effect"] == ()


def test_changed_private_value_fingerprint_is_never_exported():
    before = {"stage": "dimensions", "controls": {
        "edit:1000": {"role": "edit", "label": "Szerokość",
                      "state": {"value_present": True, "_value_fingerprint": "private-a"}},
    }}
    after = {"stage": "dimensions", "controls": {
        "edit:1000": {"role": "edit", "label": "Szerokość",
                      "state": {"value_present": True, "_value_fingerprint": "private-b"}},
    }}
    result = semantic_transition(before, after)
    assert result["changed"][0]["field_name"] == "width_1"
    assert result["changed"][0]["value_changed"] is True
    import json
    serialized = json.dumps(result)
    assert "_value_fingerprint" not in serialized
    assert "private-a" not in serialized
    assert "private-b" not in serialized
    report = construction_demonstration_report([{"type": "transition", "transition": result}])
    assert "width_1" in report["construction_groups"]["dimensions"]["fields_with_observed_effect"]
