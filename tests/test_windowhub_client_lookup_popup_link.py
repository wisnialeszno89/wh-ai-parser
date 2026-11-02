from __future__ import annotations

from tools.diagnose_windowhub_client_lookup_popup_link import (
    _geometry_relation,
)


def test_popup_directly_below_lookup_with_horizontal_overlap():
    result = _geometry_relation(
        (100, 100, 300, 130),
        (100, 131, 520, 360),
    )

    assert result == {
        "bounds_available": True,
        "horizontal_overlap": True,
        "popup_below_lookup": True,
        "vertical_gap_bucket": "0-20",
        "popup_width_relation": "wider_than_lookup",
    }


def test_popup_far_below_lookup_is_separated_by_gap_bucket():
    result = _geometry_relation(
        (100, 100, 300, 130),
        (120, 250, 520, 500),
    )

    assert result["horizontal_overlap"] is True
    assert result["popup_below_lookup"] is True
    assert result["vertical_gap_bucket"] == "81+"


def test_popup_without_horizontal_overlap_is_not_related_by_alignment():
    result = _geometry_relation(
        (100, 100, 300, 130),
        (400, 130, 800, 350),
    )

    assert result["horizontal_overlap"] is False
    assert result["popup_below_lookup"] is True


def test_missing_bounds_fail_closed():
    result = _geometry_relation(None, (100, 130, 500, 350))

    assert result == {
        "bounds_available": False,
        "horizontal_overlap": False,
        "popup_below_lookup": False,
        "vertical_gap_bucket": "unknown",
        "popup_width_relation": "unknown",
    }
