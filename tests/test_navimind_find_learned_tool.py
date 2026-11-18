"""No-input semantic discovery regression tests."""
from tools.run_navimind_find_learned_tool import (
    candidate_score, find_candidates, normalize,
)


def test_normalize_polish_tool_names():
    assert normalize("Wybór typu okuć") == "wybor typu okuc"
    assert normalize("Ościeżnica + skrzydłem") == "oscieznica skrzydlem"


def test_find_hardware_from_tooltip_evidence():
    icon_map = {
        "schema": "navimind.icon_map.unverified.v1",
        "icons": [
            {
                "label_hypothesis": "Ec . Okucia Wybor typu okué",
                "ocr_confidence": 72,
                "evidence": "ocr_candidate_unverified",
                "pointer": [120, 220],
                "relative_bounds": [100, 200, 36, 36],
            },
            {
                "label_hypothesis": "Kalkuluj oferte",
                "ocr_confidence": 92,
                "evidence": "ocr_candidate_unverified",
            },
        ],
    }
    matches = find_candidates(icon_map, "okucia")
    assert len(matches) == 1
    assert matches[0]["pointer"] == [120, 220]
    assert matches[0]["behavior_verified"] is False


def test_empty_or_unverified_tool_is_not_matched():
    icon_map = {
        "schema": "navimind.icon_map.unverified.v1",
        "icons": [
            {"label_hypothesis": "Okucia",
             "evidence": "no_visual_change"},
            {"label_hypothesis": None,
             "evidence": "ocr_candidate_unverified"},
        ],
    }
    assert find_candidates(icon_map, "okucia") == []


def test_search_never_claims_click_authority():
    assert candidate_score("okucia", "Okucia Wybor typu okuc", 80) > 0
    assert candidate_score("okucia", "Kalkuluj oferte", 100) == 0
