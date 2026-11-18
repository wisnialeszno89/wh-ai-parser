"""Pure regressions for Explorer's passive learning memory."""
from types import SimpleNamespace

from app.agent.perception.explorer_tool_memory import (
    load_memory, merge_observations, select_for_learning,
)


def element(x, y):
    return SimpleNamespace(x=x, y=y, width=36, height=36)


def known(point, text="Okucia Wybór typu okuć"):
    return {
        "pointer": list(point), "label_hypothesis": text,
        "ocr_confidence": 85, "evidence": "ocr_candidate_unverified",
        "behavior_verified": False,
    }


def test_unknown_came_first_and_known_is_not_repeated():
    candidates = [element(8, 40), element(8, 120), element(8, 200)]
    choices, stats = select_for_learning(
        candidates, [known([26, 58])], limit=3,
    )
    assert [(e.x, e.y) for e in choices] == [(8, 120), (8, 200)]
    assert stats["known_skipped"] == 1


def test_uncertain_retried_after_never_seen():
    candidates = [element(8, 40), element(8, 120)]
    uncertain = dict(known([26, 58]), evidence="visual_change_no_readable_text",
                     label_hypothesis=None)
    choices, stats = select_for_learning(candidates, [uncertain], limit=2)
    assert [(e.x, e.y) for e in choices] == [(8, 120), (8, 40)]
    assert stats["retry_uncertain"] == 1


def test_bad_second_ocr_does_not_erase_known_label():
    first = known([26, 58])
    records = [{
        "hover_at_relative": [26, 58],
        "rect_relative": [8, 40, 36, 36],
        "tooltip_ocr": {"text": None, "confidence": None,
                        "status": "no_visual_change"},
    }]
    merged = merge_observations([first], records)
    assert len(merged) == 1
    assert merged[0]["label_hypothesis"] == first["label_hypothesis"]


def test_migration_from_legacy_memory_keeps_recorded_names(tmp_path):
    import json
    path = tmp_path / "icons.json"
    path.write_text(json.dumps({
        "schema": "navimind.icon_map.unverified.v1",
        "application": "okna.exe",
        "icons": [known([26, 58])],
    }), encoding="utf-8")
    assert len(load_memory(
        path, application="okna.exe", window_title="Okna - OFR/1",
        window_size=(1920, 1080),
    )) == 1


def test_memory_is_limited_to_matching_application_window_and_size(tmp_path):
    import json
    path = tmp_path / "icons.json"
    path.write_text(json.dumps({
        "schema": "navimind.icon_map.unverified.v1",
        "application": "okna.exe",
        "window_title": "Okna - OFR/1",
        "window_size": [1920, 1080],
        "icons": [known([26, 58])],
    }), encoding="utf-8")
    assert load_memory(
        path, application="okna.exe", window_title="Okna - OFR/2",
        window_size=(1920, 1080),
    ) == []
    assert load_memory(
        path, application="okna.exe", window_title="Okna - OFR/1",
        window_size=(1280, 720),
    ) == []
