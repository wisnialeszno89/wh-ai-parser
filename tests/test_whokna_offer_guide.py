"""Pure tests for documentation-grounded WH Okna offer preflight."""
import pytest

from app.agent.knowledge.whokna_offer_guide import load_reference, offer_plan


def test_reference_has_source_and_guardrails():
    ref = load_reference()
    assert ref["source"]["url"].startswith("https://whokna.com.pl/")
    assert ref["policy"]["knowledge_is_not_action_authority"] is True


def test_guided_offer_has_ordered_stages_not_execution():
    plan = offer_plan(load_reference(), width=1500, height=1400)
    assert [stage["id"] for stage in plan["stages"]] == [
        "document", "position", "frame", "verify_sash",
        "glazing", "hardware", "prices", "review",
    ]
    assert all(stage["state"] == "not_started" for stage in plan["stages"])
    assert plan["safety"]["forbid_zlc_order_mutation"]
    assert plan["mode"] == "plan_only_no_desktop_actions"


def test_ocr_map_helps_match_hardware_without_clicking():
    learned = {
        "schema": "navimind.icon_map.unverified.v1",
        "icons": [
            {"evidence": "ocr_candidate_unverified",
             "label_hypothesis": "Okucia Wybor typu okuc",
             "ocr_confidence": 89,
             "pointer": [26, 810],
             "relative_bounds": [8, 792, 36, 36]},
        ],
    }
    plan = offer_plan(
        load_reference(), width=1500, height=1400, icon_map=learned
    )
    hardware = next(x for x in plan["stages"] if x["id"] == "hardware")
    assert len(hardware["tool_hypotheses"]) == 1
    assert hardware["tool_hypotheses"][0]["behavior_verified"] is False
    assert hardware["source_rules"][0]["source_pages"]


@pytest.mark.parametrize("width,height,qty", [
    (0, 1400, 1), (1500, 20000, 1), (1500, 1400, 0),
])
def test_invalid_dimensions_or_quantity_rejected(width, height, qty):
    with pytest.raises(ValueError):
        offer_plan(load_reference(), width=width, height=height, quantity=qty)


def test_does_not_assume_sash_click_when_frame_type_autoinserts_it():
    plan = offer_plan(load_reference(), width=1500, height=1400)
    sash = next(x for x in plan["stages"] if x["id"] == "verify_sash")
    assert "Sprawdź" in sash["title"]
    assert sash["requires_test_offer_for_write"] is False


def test_tooltip_szklenia_matches_glazing_stage():
    learned = {
        "schema": "navimind.icon_map.unverified.v1",
        "icons": [{
            "evidence": "ocr_candidate_unverified",
            "label_hypothesis": "Szklenia Wstawianie szklenia",
            "ocr_confidence": 88,
            "pointer": [26, 620],
            "relative_bounds": [8, 602, 36, 36],
        }],
    }
    stages = offer_plan(
        load_reference(), width=1500, height=1400, icon_map=learned
    )["stages"]
    glazing = next(s for s in stages if s["id"] == "glazing")
    assert glazing["tool_hypotheses"]
    assert glazing["tool_hypotheses"][0]["behavior_verified"] is False
