from copy import deepcopy

import pytest

from app.agent.offers.windowhub_existing_offer_lab import ExistingOfferLab
from tools.check_windowhub_existing_offer_flow import load_fixture, run_headless, verify_saved


def test_correction_replaces_reference_regardless_of_list_order_and_preserves_other_offer():
    scenario, offers = load_fixture()
    original = deepcopy(offers)
    report = run_headless(scenario, offers)
    verify_saved(report, original, scenario)
    assert [row["reference"] for row in report["offer"]["positions"]] == ["20.0", "10.0"]
    assert offers[0] == original[0]
    assert report["offer"]["positions"][0]["simulation"]["active_side"] == "right"
    assert len(report["offer"]["positions"]) == 2


def test_unknown_offer_and_position_leave_source_unchanged():
    scenario, offers = load_fixture()
    original = deepcopy(offers)
    flow = ExistingOfferLab(offers)
    flow.existing_offer()
    with pytest.raises(ValueError, match="numeru oferty"):
        flow.load("missing")
    flow.load(scenario["offer_number"])
    with pytest.raises(ValueError, match="numeru pozycji"):
        flow.select_position("30.0")
    assert offers == original


def test_failed_build_and_stale_offer_cannot_be_saved():
    scenario, offers = load_fixture()
    flow = ExistingOfferLab(offers)
    flow.existing_offer()
    flow.load(scenario["offer_number"])
    flow.select_position(scenario["position_reference"])
    with pytest.raises(ValueError, match="podziału"):
        flow.correct({"kind": "stulp", "specification": {
            "mullion": "movable", "active_side": "right", "right_opening": "DKR", "glazing_panes": 3,
        }})
    assert flow.stage == "edit"
    flow.correct(scenario["changes"])
    offers[1]["revision"] += 1
    original = deepcopy(offers)
    with pytest.raises(ValueError, match="zmieniła się"):
        flow.save()
    assert offers == original


def test_second_save_cannot_append_or_repeat_commit():
    scenario, offers = load_fixture()
    flow = ExistingOfferLab(offers)
    flow.existing_offer()
    flow.load(scenario["offer_number"])
    flow.select_position(scenario["position_reference"])
    flow.correct(scenario["changes"])
    flow.save()
    with pytest.raises(ValueError, match="Oczekiwano"):
        flow.save()
    assert offers[1]["revision"] == 2 and len(offers[1]["positions"]) == 2
