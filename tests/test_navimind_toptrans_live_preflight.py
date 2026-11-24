"""Top Trans acceptance is a bounded data contract, not a fake GUI test."""
import json
import pytest

from app.agent.runtime.navimind_toptrans_live_preflight import (
    top_trans_acceptance, top_trans_report,
)


def test_default_contract_preserves_all_explicit_customer_requirements():
    plan = top_trans_acceptance()
    assert plan.customer == "Top Trans"
    assert len(plan.positions) == 2
    a, b = plan.positions
    assert (a.position, a.quantity, a.leaves) == (1, 1, 1)
    assert (a.colour_inside, a.colour_outside) == ("biały", "biały")
    assert (b.position, b.quantity, b.leaves) == (2, 1, 2)
    assert b.glazing_panes == 2
    assert "montaż" in plan.hide_prices
    assert "demontaż" in plan.hide_prices
    assert "wykończenie" in plan.hide_prices
    assert plan.show_construction_price


def test_unknown_dimensions_are_never_replaced_by_ui_defaults():
    plan = top_trans_acceptance()
    assert all(p.width_mm is None and p.height_mm is None for p in plan.positions)
    assert "position_1:width_mm" in plan.missing
    assert "position_2:height_mm" in plan.missing
    assert not plan.live_gui_actions_authorized


def test_single_sided_colour_needs_direction_confirmation():
    p = top_trans_acceptance()
    assert p.positions[1].colour_inside is None
    assert p.positions[1].colour_outside is None
    assert "position_2:anthracite_side" in p.missing
    p = top_trans_acceptance(anthracite_side="outside")
    assert p.positions[1].colour_inside == "biały"
    assert p.positions[1].colour_outside == "antracyt struktura 701605"


def test_first_glazing_is_a_proposal_not_fabricated_customer_requirement():
    p = top_trans_acceptance()
    assert p.positions[0].glazing_panes is None
    assert "position_1:glazing_panes" in p.missing
    assert "position_1:2_panes_as_default_proposal" in p.assumptions_to_confirm
    confirmed = top_trans_acceptance(confirm_first_glazing=2)
    assert confirmed.positions[0].glazing_panes == 2


def test_fully_specified_request_still_does_not_authorize_live_gui():
    p = top_trans_acceptance(
        widths_mm=(1200, 1400), heights_mm=(1400, 1500),
        opening=("left", "main_right"), anthracite_side="outside",
        confirm_first_glazing=2,
    )
    assert p.missing == ()
    assert p.status == "REVIEW_ONLY"
    assert not p.live_gui_actions_authorized
    assert not p.save_authorized
    assert not p.sent_to_customer
    payload = json.loads(p.serialize())
    assert payload["positions"][1]["width_mm"] == 1400


@pytest.mark.parametrize("change", [
    {"widths_mm": (0, None)}, {"heights_mm": (None, 99999)},
    {"widths_mm": (1000.5, None)}, {"opening": ("random", None)},
    {"anthracite_side": "both"}, {"confirm_first_glazing": 8},
])
def test_invalid_values_fail_closed(change):
    with pytest.raises(ValueError):
        top_trans_acceptance(**change)


def test_report_does_not_invent_completion():
    output = top_trans_report()
    assert "NAVIMIND_TOP_TRANS_PREFLIGHT=REVIEW_ONLY" in output
    assert "POSITIONS=2" in output
    assert "NATIVE_V2_EXECUTOR_CONNECTED=False" in output
    assert "REAL_WINDOWHUB_ACTIONS=0" in output
