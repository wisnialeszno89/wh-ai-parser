from copy import deepcopy
import json

import pytest

from app.agent.intake.windowhub_sales_correction import parse_sales_correction, resolve_sales_correction
from tools.check_windowhub_existing_offer_flow import load_fixture, run_headless, verify_saved
from tools.check_windowhub_sales_correction import main

COMMAND = "W ofercie 101 zmień pozycję 20 na 1800 x 1500 mm, słupek ruchomy, prawe skrzydło czynne, podział 900 mm od lewej."


def test_text_command_reaches_saved_offer_through_normal_entry_point(tmp_path):
    output = tmp_path / "offer.json"
    assert main(["--command", COMMAND, "--headless", "--output", str(output)]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["command"] == COMMAND
    assert report["offer"]["number"] == "OFR/TEST/2026/101"
    assert report["changed_position"] == "20.0"
    changed, first = report["offer"]["positions"]
    assert changed["simulation"]["active_side"] == "right"
    assert (changed["width_mm"], changed["height_mm"]) == (1800, 1500)
    assert changed["specification"]["right_opening"] == "DKR"
    assert (first["width_mm"], first["height_mm"]) == (1000, 1000)
    assert len(report["offer"]["positions"]) == 2


def test_second_text_actually_selects_another_position_and_size():
    _, offers = load_fixture()
    original = deepcopy(offers)
    command = "W ofercie OFR/TEST/2026/101 zmien pozycje 10.0 na 1100 × 1200."
    scenario = resolve_sales_correction(command, offers)
    report = run_headless(scenario, offers)
    verify_saved(report, original, scenario)
    changed = next(row for row in report["offer"]["positions"] if row["reference"] == "10.0")
    assert changed["simulation"]["direction"] == "RIGHT"
    assert (changed["width_mm"], changed["height_mm"]) == (1100, 1200)
    assert report["offer"]["positions"][0] == original[1]["positions"][0]


@pytest.mark.parametrize("command", [
    COMMAND + " Dodaj rabat 10%.",
    "W ofercie 101 zmień pozycję 20 na 0 x 1500",
    "W ofercie 101 zmień pozycję 20 na 1800 x 1500 cm",
    "Usuń wszystkie oferty",
])
def test_unrecognized_or_additional_instructions_are_not_ignored(command):
    with pytest.raises(ValueError):
        parse_sales_correction(command)


def test_missing_split_requires_review_without_modifying_loaded_offers():
    _, offers = load_fixture()
    original = deepcopy(offers)
    with pytest.raises(ValueError, match="podział"):
        resolve_sales_correction(
            "W ofercie 101 zmień pozycję 20 na 1800 x 1500, słupek ruchomy, prawe czynne", offers,
        )
    assert offers == original


def test_ambiguous_short_number_and_missing_position_require_review():
    _, offers = load_fixture()
    extra = deepcopy(offers[1])
    extra["number"] = "OFR/OTHER/2026/101"
    with pytest.raises(ValueError, match="Numer oferty"):
        resolve_sales_correction(COMMAND, offers + [extra])
    with pytest.raises(ValueError, match="Numer pozycji"):
        resolve_sales_correction(COMMAND.replace("pozycję 20", "pozycję 30"), offers)
