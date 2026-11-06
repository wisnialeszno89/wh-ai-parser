"""Read-only construction hit-root evidence must not claim component completion."""
from types import SimpleNamespace

import pytest

from app.agent.learning.windowhub_drawing_candidate_evidence import (
    check_drawing_candidate_owner,
)

WINDOW = SimpleNamespace(left=-4, top=0, width=992, height=1150)
RECT = SimpleNamespace(x=73, y=455, width=233, height=469)


def evidence(**overrides):
    args = dict(
        window_rect=WINDOW, candidate_rect=RECT,
        offer_hwnd=100, foreground_hwnd=100, hit_root_hwnd=100,
    )
    args.update(overrides)
    return check_drawing_candidate_owner(**args)


def test_candidate_center_is_inside_observed_offer_window():
    found = evidence()
    assert found.point == (185, 689)
    assert found.status == "owned_pixel_not_component_verified"
    assert found.root_matches is True
    assert "not_verified" in found.reason


def test_different_foreground_refuses_candidate_owner():
    assert evidence(foreground_hwnd=999).status == "rejected"
    assert evidence(foreground_hwnd=999).reason == "offer_lost_foreground"


def test_foreign_root_refuses_candidate_owner():
    assert evidence(hit_root_hwnd=500).status == "rejected"
    assert evidence(hit_root_hwnd=500).reason == "pixel_owned_by_other_root_window"


def test_outside_candidate_refused_without_point():
    found = evidence(candidate_rect=SimpleNamespace(x=980, y=450, width=50, height=50))
    assert found.status == "rejected"
    assert found.point is None


def test_no_candidate_does_not_claim_detection():
    assert evidence(candidate_rect=None).status == "not_observed"


def test_invalid_window_identity_is_refused():
    with pytest.raises(ValueError, match="invalid_window_identity"):
        evidence(offer_hwnd=0)
