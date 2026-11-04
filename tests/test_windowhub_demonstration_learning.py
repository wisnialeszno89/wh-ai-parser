from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.learning.windowhub_demonstration import (
    semantic_snapshot, semantic_transition, demonstration_experience, stage_of,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def scene(title, *, checked=False, value="PERSONAL CUSTOMER 123", app="Okna.exe"):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application=app, active_window_title=title)
        ),
        elements=(
            ScreenElement(
                kind="checkbox", label="OknaWPF",
                metadata={
                    "source": "windowhub_ui_automation",
                    "uia_visible": True, "uia_enabled": True,
                    "uia_checked": checked,
                    "automation_id": "IDC_CENA_OKNA",
                    "current_value": value,
                    "semantic_label": "Bez ceny konstrukcji",
                },
            ),
        ),
    )


def test_demo_records_state_changes_but_never_business_values():
    before = semantic_snapshot(scene("Właściwości dokumentu", checked=False))
    after = semantic_snapshot(scene("Właściwości dokumentu", checked=True))
    transition = semantic_transition(before, after)
    assert transition["from_stage"] == "document_properties"
    assert transition["to_stage"] == "document_properties"
    assert transition["changed"][0]["label"] == "Bez ceny konstrukcji"
    assert transition["changed"][0]["before"]["checked"] is False
    assert transition["changed"][0]["after"]["checked"] is True
    assert "PERSONAL CUSTOMER" not in str(before)
    assert "PERSONAL CUSTOMER" not in str(after)
    assert "PERSONAL CUSTOMER" not in str(transition)


def test_manual_stage_changes_are_evidence_not_assumed_clicks():
    first = semantic_snapshot(scene("Okna - Start1"))
    second = semantic_snapshot(scene("Właściwości dokumentu"))
    change = semantic_transition(first, second)
    assert change["from_stage"] == "start"
    assert change["to_stage"] == "document_properties"
    experience = demonstration_experience([
        {"type": "transition", "transition": change},
        {"type": "transition", "transition": change},
        {"type": "other", "transition": change},
    ])
    assert len(experience) == 1
    assert experience[0]["certainty"] == "observed_transition_not_causal_action"


def test_switching_apps_does_not_log_foreign_window():
    assert semantic_snapshot(scene("password manager", app="Other.exe")) is None
    assert stage_of(scene("Okna - OFR/12345- <>")) == "offer_document"


def test_duplicated_native_field_is_omitted_in_demo_snapshot():
    s = scene("Właściwości dokumentu")
    duplicated = ScreenScene(observation=s.observation, elements=(s.elements[0], s.elements[0]))
    assert semantic_snapshot(duplicated)["controls"] == {}


def test_reuse_real_form_effects_as_noncausal_nameless_training_experience():
    before = semantic_snapshot(scene("Właściwości dokumentu", checked=False))
    after = semantic_snapshot(scene("Właściwości dokumentu", checked=True))
    event = {"type": "transition", "transition": semantic_transition(before, after)}
    experience = demonstration_experience([event])
    assert len(experience) == 1
    assert experience[0]["control"] == "Bez ceny konstrukcji"
    assert experience[0]["observed_state"] == "checked"
    assert experience[0]["observed_value"] is True
    assert experience[0]["certainty"] == "observed_effect_not_causal_action"
    assert "PERSONAL CUSTOMER" not in str(experience)
    assert "IDC_CENA_OKNA" not in str(experience)


def test_demo_report_reuses_recording_and_exposes_missing_modifier():
    from app.agent.learning.windowhub_demonstration import demonstration_summary

    first = semantic_snapshot(scene("Okna - Start1"))
    second = semantic_snapshot(scene("Właściwości dokumentu"))
    third = semantic_snapshot(scene("Dodawanie nowej pozycji"))
    unknown = semantic_snapshot(scene("Nieznany etap WindowHub"))
    records = [
        {"type": "transition", "transition": semantic_transition(first, second)},
        {"type": "transition", "transition": semantic_transition(second, third)},
        {"type": "transition", "transition": semantic_transition(third, unknown)},
    ]
    report = demonstration_summary(records)
    assert report["record_count"] == 3
    assert report["stage_sequence"] == (
        "start", "document_properties", "position", "windowhub_unmapped",
    )
    assert report["unmapped_transitions"] == 1
    assert report["modifier_observed"] is False
    assert report["model_experience_items"] == 2
