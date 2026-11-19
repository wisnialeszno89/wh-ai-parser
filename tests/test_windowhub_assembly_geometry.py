"""No manufacturer sizing values are fabricated in dimension reconciliation."""
from app.agent.knowledge.windowhub_assembly_geometry import (
    AssemblyDimensions, HeightConvention, reconcile_assembly, reconcile_window_and_box,
)


def test_total_envelope_subtracts_only_verified_box():
    x = reconcile_assembly(AssemblyDimensions(
        1020, 1400, 205, HeightConvention.INCLUDED_IN_TOTAL,
        convention_verified=True, minimum_window_height_mm=700,
    ))
    assert x.status == "planned_requires_live_readback"
    assert x.window_height_mm == 1195
    assert x.combined_height_mm == 1400


def test_unverified_mounting_rule_cannot_drive_program():
    x = reconcile_assembly(AssemblyDimensions(
        1020, 1400, 205, HeightConvention.INCLUDED_IN_TOTAL,
    ))
    assert x.status == "requires_catalogue_evidence"


def test_unknown_box_size_cannot_be_guessed():
    x = reconcile_window_and_box(
        window_height_mm=1010, box_height_mm=None, box_height_verified=False,
    )
    assert x.status == "requires_catalogue_evidence"
    assert x.window_height_mm == 1010
    assert x.combined_height_mm is None


def test_bare_window_dimension_not_reduced_for_box():
    x = reconcile_window_and_box(
        window_height_mm=1010, box_height_mm=205, box_height_verified=True,
    )
    assert x.window_height_mm == 1010
    assert x.combined_height_mm == 1215


def test_explicit_envelope_conflict_is_not_ignored():
    x = reconcile_window_and_box(
        window_height_mm=1010, box_height_mm=205, box_height_verified=True,
        requested_total_height_mm=1200,
    )
    assert x.status == "blocked"


def test_verified_product_size_constraints_apply():
    x = reconcile_assembly(AssemblyDimensions(
        800, 700, 250, HeightConvention.INCLUDED_IN_TOTAL,
        convention_verified=True, minimum_window_height_mm=500,
    ))
    assert x.status == "blocked"
