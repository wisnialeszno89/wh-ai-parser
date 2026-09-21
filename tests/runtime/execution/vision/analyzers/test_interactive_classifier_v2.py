from app.runtime.execution.vision.analyzers.interactive_classifier_v2 import (
    InteractiveClassifierV2,
)
from app.runtime.execution.vision.models.logical_object_evidence import (
    LogicalObjectEvidence,
)
from app.runtime.execution.vision.models.visual_features import VisualFeatures
from app.runtime.execution.vision.models.control_type import ControlType


def evidence(
    *,
    width: int,
    height: int,
    member_count: int,
    edge: float,
    border: float,
    interior: float,
) -> LogicalObjectEvidence:
    return LogicalObjectEvidence(
        width=width,
        height=height,
        area=width * height,
        aspect_ratio=width / float(height) if height else 0.0,
        area_ratio=0.001,
        member_count=member_count,
        child_count=max(0, member_count - 1),
        visual=VisualFeatures(
            edge_density=edge,
            border_edge_density=border,
            horizontal_edge_density=0.1,
            vertical_edge_density=0.1,
            contour_density=0.01,
            dark_pixel_ratio=0.05,
            bright_pixel_ratio=0.8,
            interior_content_density=interior,
        ),
    )


def test_classifies_dodaj_like_object_as_button():
    result = InteractiveClassifierV2().classify(
        evidence(
            width=56,
            height=21,
            member_count=2,
            edge=0.330,
            border=0.121,
            interior=0.126,
        )
    )

    assert result.control_type == ControlType.BUTTON
    assert result.is_interactive
    assert result.confidence > 0.0


def test_classifies_square_visual_object_as_icon():
    result = InteractiveClassifierV2().classify(
        evidence(
            width=28,
            height=28,
            member_count=3,
            edge=0.334,
            border=0.074,
            interior=0.396,
        )
    )

    assert result.control_type == ControlType.ICON
    assert not result.is_interactive
    assert result.confidence > 0.0


def test_rejects_form_field_as_button():
    result = InteractiveClassifierV2().classify(
        evidence(
            width=97,
            height=33,
            member_count=2,
            edge=0.109,
            border=0.002,
            interior=0.086,
        )
    )

    assert result.control_type == ControlType.UNKNOWN


def test_rejects_text_like_object_as_button():
    result = InteractiveClassifierV2().classify(
        evidence(
            width=65,
            height=33,
            member_count=2,
            edge=0.069,
            border=0.003,
            interior=0.020,
        )
    )

    assert result.control_type == ControlType.UNKNOWN


def test_rejects_large_object():
    result = InteractiveClassifierV2().classify(
        evidence(
            width=475,
            height=41,
            member_count=5,
            edge=0.189,
            border=0.036,
            interior=0.311,
        )
    )

    assert result.control_type == ControlType.UNKNOWN
