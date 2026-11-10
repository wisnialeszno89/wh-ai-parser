from tools.check_windowhub_mixed_offer import prepare_mixed_offer, sample_positions


def test_mixed_handoff_continues_after_incomplete_position():
    source = {"status": "technical_draft", "positions": [{
        "position": "10.0", "construction": "F004 DK-Fenster", "system": "Zirkon",
        "width_mm": 935, "height_mm": 1145, "quantity": 1, "opening": "DKL",
    }]}
    single, complete, incomplete = sample_positions(source)

    report = prepare_mixed_offer([single, incomplete, complete])
    first, second, third = report["positions"]

    assert report["status"] == "sales_review_required"
    assert first["status"] == "simulated"
    assert first["source"] == source["positions"][0]
    assert first["simulation"]["final_direction"] == "LEFT"
    assert second["status"] == "review"
    assert "Brakuje wymiaru podziału" in second["reason"]
    assert "steps" not in second
    assert third["status"] == "planned"
    assert third["steps"][1]["parameters"]["offset_from_left_mm"] == 650
    assert third["steps"][-1]["side"] == "RIGHT"
