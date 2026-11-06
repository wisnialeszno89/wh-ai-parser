"""Visual structure hints do not become verified window component identities."""
from types import SimpleNamespace

from app.agent.learning.windowhub_visual_structure_evidence import visual_structure_hints


def line(x, strength):
    return SimpleNamespace(coordinate=x, strength=strength)


def sample():
    return SimpleNamespace(
        construction_rect=(73, 455, 233, 469),
        vertical_lines=(line(0, 1.0), line(112, 0.3), line(231, 0.8)),
        horizontal_lines=(line(5, 0.8), line(240, 0.1), line(450, 0.8)),
        cells=(object(), object()),
    )


def test_external_window_owner_refuses_geometry():
    hints = visual_structure_hints(sample(), "rejected")
    assert hints["status"] == "blocked_unverified_window_owner"
    assert hints["cell_candidates"] == 0


def test_verified_owner_exposes_only_tentative_internal_lines():
    hints = visual_structure_hints(sample(), "owned_pixel_not_component_verified")
    assert hints["status"] == "geometry_hints_only"
    assert hints["vertical_internal_candidates"] == ((112, 0.3),)
    assert hints["horizontal_internal_candidates"] == ()
    assert hints["cell_candidates"] == 2
    assert hints["components_verified"] == 0


def test_missing_geometry_is_not_accepted():
    hints = visual_structure_hints(SimpleNamespace(construction_rect=None), "owned_pixel_not_component_verified")
    assert hints["status"] == "blocked_missing_geometry"
    assert hints["components_verified"] == 0
