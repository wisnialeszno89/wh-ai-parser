import json

import pytest

from app.agent.offers.windowhub_offer_workflow_lab import OfferWorkflowLab
from tools.check_windowhub_two_position_flow import ROOT, run_headless, verify_saved


def scenario():
    return json.loads((ROOT / "examples/windowhub-two-position-flow.json").read_text(encoding="utf-8"))


def test_two_positions_are_independent_and_only_saved_after_building():
    request = scenario()
    report = run_headless(request)
    verify_saved(report, request)
    first, second = report["positions"]
    assert first["simulation"]["direction"] == "RIGHT"
    assert second["simulation"]["final_directions"] == {"left": "LEFT", "right": "RIGHT"}
    assert [e["kind"] for e in first["simulation"]["scene"]["elements"]] == ["FRAME", "SASH", "GLASS"]
    assert any(e["kind"] == "MULLION" for e in second["simulation"]["scene"]["elements"])
    assert [step["to"] for step in report["trace"]].count("item_type") == 2
    assert report["status"] == "sales_review_required"
    assert report["trace"][-1]["saved_positions"] == 2


def test_preferences_and_partial_build_do_not_commit_a_position():
    flow = OfferWorkflowLab()
    flow.new_offer()
    document = scenario()["document"]
    with pytest.raises(ValueError, match="Top Trans"):
        flow.confirm_document(dict(document, customer="Top Trans S.A."))
    assert flow.stage == "document"
    flow.confirm_document(document)
    flow.select_window("double_fixed")
    flow.set_dimensions(1, 1500, 1400)
    flow.set_color("biały", "antracyt")
    with pytest.raises(ValueError, match="podziału"):
        flow.build({"mullion": "fixed", "glazing_panes": 3})
    assert flow.stage == "builder"
    assert flow.positions == []
    with pytest.raises(ValueError, match="Oczekiwano"):
        flow.add_position()
