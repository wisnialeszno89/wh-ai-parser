import json

from app.agent.learning.windowhub_training_context import (
    read_demonstration_experience, read_demonstration_report,
)
from tools.report_windowhub_demonstration import main as report_main


def test_old_style_recording_is_readable_and_reports_coverage(tmp_path, capsys):
    recording = tmp_path / "demo.jsonl"
    records = [
        {"type": "session", "version": 1, "goal": "Manual WindowHub tutorial"},
        {"type": "transition", "transition": {
            "from_stage": "start", "to_stage": "document_properties",
            "changed": [],
        }},
        {"type": "transition", "transition": {
            "from_stage": "document_properties", "to_stage": "position",
            "changed": [],
        }},
        {"type": "transition", "transition": {
            "from_stage": "position", "to_stage": "dimensions",
            "changed": [],
        }},
        {"type": "transition", "transition": {
            "from_stage": "basic_parameters", "to_stage": "windowhub_unmapped",
            "changed": [],
        }},
    ]
    recording.write_text(
        "\n".join(json.dumps(item) for item in records) + "\n",
        encoding="utf-8",
    )
    report = read_demonstration_report(recording)
    assert report["record_count"] == 4
    assert report["modifier_observed"] is False
    assert report["unmapped_transitions"] == 1
    learned = read_demonstration_experience(recording)
    assert len(learned) == 3

    assert report_main(["--demo", str(recording)]) == 0
    output = capsys.readouterr().out
    assert "LEARNED_TRANSITION=start -> document_properties" in output
    assert "NEXT_GAP=Modifier" in output


def test_old_style_form_state_changes_become_model_context(tmp_path):
    recording = tmp_path / "demo.jsonl"
    recording.write_text(json.dumps({
        "type": "transition",
        "transition": {
            "from_stage": "document_properties",
            "to_stage": "document_properties",
            "changed": [{
                "role": "checkbox", "label": "Bez ceny konstrukcji",
                "before": {"checked": False},
                "after": {"checked": True},
            }],
        },
    }) + "\n", encoding="utf-8")
    experience = read_demonstration_experience(recording)
    assert len(experience) == 1
    assert experience[0]["control"] == "Bez ceny konstrukcji"
    assert experience[0]["observed_value"] is True
