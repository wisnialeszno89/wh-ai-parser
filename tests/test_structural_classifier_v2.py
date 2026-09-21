from app.runtime.execution.vision.analyzers.structural_classifier_v2 import (
    StructuralClassifierV2,
)
from app.runtime.execution.vision.models.candidate_features import (
    CandidateFeatures,
)
from app.runtime.execution.vision.models.control_type import ControlType


def features(
    *,
    width=100,
    height=100,
    area=10_000,
    aspect_ratio=1.0,
    area_ratio=0.05,
    width_ratio=0.05,
    height_ratio=0.05,
    center_x=0.5,
    center_y=0.5,
    depth=0,
    child_count=0,
    sibling_count=0,
    touches_left=False,
    touches_right=False,
    touches_top=False,
    touches_bottom=False,
):
    return CandidateFeatures(
        width=width,
        height=height,
        area=area,
        aspect_ratio=aspect_ratio,
        area_ratio=area_ratio,
        width_ratio=width_ratio,
        height_ratio=height_ratio,
        center_x=center_x,
        center_y=center_y,
        depth=depth,
        child_count=child_count,
        sibling_count=sibling_count,
        touches_left=touches_left,
        touches_right=touches_right,
        touches_top=touches_top,
        touches_bottom=touches_bottom,
    )


def test_detects_horizontal_toolbar_from_context():
    result = StructuralClassifierV2().classify(
        [
            features(
                width=900,
                height=60,
                aspect_ratio=15.0,
                area_ratio=0.05,
                width_ratio=0.50,
                height_ratio=0.05,
                child_count=6,
                sibling_count=2,
            )
        ]
    )[0]

    assert result.control_type == ControlType.TOOLBAR
    assert result.child_count == 6
    assert result.confidence > 0.85


def test_detects_vertical_toolbar():
    result = StructuralClassifierV2().classify(
        [
            features(
                width=100,
                height=600,
                aspect_ratio=100 / 600,
                area_ratio=0.05,
                width_ratio=0.05,
                height_ratio=0.52,
                child_count=5,
            )
        ]
    )[0]

    assert result.control_type == ControlType.TOOLBAR


def test_detects_smaller_square_canvas():
    result = StructuralClassifierV2().classify(
        [
            features(
                width=317,
                height=317,
                aspect_ratio=1.0,
                area_ratio=0.045,
                width_ratio=0.165,
                height_ratio=0.276,
                child_count=0,
                sibling_count=1,
            )
        ]
    )[0]

    assert result.control_type == ControlType.CANVAS


def test_detects_panel_using_children():
    result = StructuralClassifierV2().classify(
        [
            features(
                width=500,
                height=400,
                aspect_ratio=1.25,
                area_ratio=0.18,
                width_ratio=0.26,
                height_ratio=0.35,
                child_count=4,
                depth=0,
            )
        ]
    )[0]

    assert result.control_type == ControlType.PANEL
    assert result.child_count == 4


def test_detects_section_from_multiple_children():
    result = StructuralClassifierV2().classify(
        [
            features(
                width=300,
                height=200,
                aspect_ratio=1.5,
                area_ratio=0.04,
                width_ratio=0.16,
                height_ratio=0.17,
                child_count=3,
                depth=1,
            )
        ]
    )[0]

    assert result.control_type == ControlType.SECTION


def test_keeps_ambiguous_candidate_unknown():
    result = StructuralClassifierV2().classify(
        [
            features(
                width=97,
                height=33,
                aspect_ratio=97 / 33,
                area_ratio=0.001,
                width_ratio=0.05,
                height_ratio=0.03,
                child_count=0,
                sibling_count=11,
            )
        ]
    )[0]

    assert result.control_type == ControlType.UNKNOWN
    assert result.confidence == 0.40


def test_classification_preserves_input_order():
    result = StructuralClassifierV2().classify(
        [
            features(
                width=900,
                height=60,
                aspect_ratio=15.0,
                area_ratio=0.05,
                width_ratio=0.50,
                height_ratio=0.05,
                child_count=5,
            ),
            features(
                width=97,
                height=33,
                aspect_ratio=97 / 33,
                area_ratio=0.001,
                width_ratio=0.05,
                height_ratio=0.03,
            ),
        ]
    )

    assert result[0].control_type == ControlType.TOOLBAR
    assert result[1].control_type == ControlType.UNKNOWN
