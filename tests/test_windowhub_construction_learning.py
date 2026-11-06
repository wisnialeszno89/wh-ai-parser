"""Construction learning must not infer component choices from stage changes."""
from app.agent.learning.windowhub_construction_learning import (
    construction_map_coverage,
    construction_demonstration_report,
    construction_learning_experience,
)


def test_existing_offer_map_has_core_frame_glazing_and_hardware_fields():
    coverage = construction_map_coverage()
    assert coverage["mapped_groups"]["frame_system"]["status"] == "uia_mapped_not_business_validated"
    assert coverage["mapped_groups"]["glazing"]["status"] == "uia_mapped_not_business_validated"
    assert coverage["mapped_groups"]["hardware"]["status"] == "uia_mapped_not_business_validated"
    assert "sash_profile" in coverage["pending_groups"]


def test_demo_learning_tracks_steps_but_does_not_invent_construction_specs():
    records = [
        {"type": "transition", "transition": {
            "from_stage": "dimensions", "to_stage": "basic_parameters", "changed": []
        }},
        {"type": "transition", "transition": {
            "from_stage": "basic_parameters", "to_stage": "glazing", "changed": []
        }},
        {"type": "transition", "transition": {
            "from_stage": "glazing", "to_stage": "hardware", "changed": []
        }},
    ]
    report = construction_demonstration_report(records)
    assert report["construction_groups"]["dimensions"]["stage_observed"]
    assert report["construction_groups"]["glazing"]["stage_observed"]
    assert report["construction_groups"]["hardware"]["stage_observed"]
    assert not report["catalog_compatibility_verified"]
    assert not report["frame_sash_topology_learned"]
    assert report["construction_groups"]["glazing"]["fields_with_observed_effect"] == ()


def test_value_changes_are_reduced_to_boolean_effect_only():
    records = [{"type": "transition", "transition": {
        "from_stage": "glazing", "to_stage": "glazing",
        "changed": [
            {"label": "Wybierz typ pakietu szybowego", "role": "combobox",
             "before": {"value_present": False, "value": "SENSITIVE"},
             "after": {"value_present": True, "value": "CUSTOM PACKAGE"}},
            {"label": "Client Name", "role": "edit",
             "before": {"value_present": False},
             "after": {"value_present": True}},
        ],
    }}]
    report = construction_demonstration_report(records)
    assert "glazing_package" in report["construction_groups"]["glazing"]["fields_with_observed_effect"]
    experience = construction_learning_experience(records)
    assert experience
    assert "SENSITIVE" not in repr(experience)
    assert "CUSTOM PACKAGE" not in repr(experience)
    assert "Client Name" not in repr(experience)


def test_empty_demo_keeps_unverified_parts_explicit():
    report = construction_demonstration_report([])
    assert not report["frame_sash_topology_learned"]
    assert report["construction_groups"]["frame_system"]["stage_observed"] is False
    assert construction_learning_experience([]) == ()
