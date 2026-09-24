from app.runtime.execution.vision.analyzers.interactive_classifier_v2 import (
    InteractiveClassifierV2,
)
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.logical_object_evidence import (
    LogicalObjectEvidence,
)
from app.runtime.execution.vision.models.visual_features import VisualFeatures


def make_evidence(
    *,
    width=56,
    height=33,
    aspect_ratio=56 / 33,
    area_ratio=0.001,
    member_count=2,
    child_count=0,
    edge_density=0.30,
    border_edge_density=0.10,
    interior_content_density=0.10,
):
    return LogicalObjectEvidence(
        width=width,
        height=height,
        area=width * height,
        aspect_ratio=aspect_ratio,
        area_ratio=area_ratio,
        member_count=member_count,
        child_count=child_count,
        visual=VisualFeatures(
            edge_density=edge_density,
            border_edge_density=border_edge_density,
            horizontal_edge_density=0.0,
            vertical_edge_density=0.0,
            contour_density=0.0,
            dark_pixel_ratio=0.0,
            bright_pixel_ratio=0.0,
            interior_content_density=interior_content_density,
        ),
    )


def test_strong_button_is_classified_as_button():
    result = InteractiveClassifierV2().classify(
        make_evidence(
            width=56,
            height=21,
            aspect_ratio=56 / 21,
            member_count=2,
            edge_density=0.30,
            border_edge_density=0.10,
            interior_content_density=0.10,
        )
    )
    assert result.control_type == ControlType.BUTTON
    assert result.is_interactive
    assert result.confidence > 0.0


def test_button_requires_minimum_edge_density():
    result = InteractiveClassifierV2().classify(
        make_evidence(edge_density=0.19)
    )
    assert result.control_type == ControlType.UNKNOWN
    assert not result.is_interactive


def test_button_requires_border_evidence():
    result = InteractiveClassifierV2().classify(
        make_evidence(border_edge_density=0.07)
    )
    assert result.control_type == ControlType.UNKNOWN
    assert not result.is_interactive


def test_button_rejects_dense_interior():
    result = InteractiveClassifierV2().classify(
        make_evidence(interior_content_density=0.26)
    )
    assert result.control_type == ControlType.UNKNOWN
    assert not result.is_interactive


def test_button_requires_multiple_members():
    result = InteractiveClassifierV2().classify(
        make_evidence(member_count=1)
    )
    assert result.control_type == ControlType.UNKNOWN
    assert not result.is_interactive


def test_button_rejects_too_narrow_geometry():
    result = InteractiveClassifierV2().classify(
        make_evidence(
            width=29,
            height=20,
            aspect_ratio=29 / 20,
        )
    )
    assert result.control_type == ControlType.UNKNOWN
    assert not result.is_interactive


def test_button_rejects_excessive_height():
    result = InteractiveClassifierV2().classify(
        make_evidence(
            width=80,
            height=46,
            aspect_ratio=80 / 46,
        )
    )
    assert result.control_type == ControlType.UNKNOWN
    assert not result.is_interactive


def test_button_rejects_excessive_aspect_ratio():
    result = InteractiveClassifierV2().classify(
        make_evidence(
            width=200,
            height=20,
            aspect_ratio=10.0,
        )
    )
    assert result.control_type == ControlType.UNKNOWN
    assert not result.is_interactive


def test_icon_is_classified_as_icon():
    result = InteractiveClassifierV2().classify(
        make_evidence(
            width=32,
            height=32,
            aspect_ratio=1.0,
            member_count=2,
            edge_density=0.25,
            border_edge_density=0.02,
            interior_content_density=0.45,
        )
    )
    assert result.control_type == ControlType.ICON
    assert not result.is_interactive
    assert result.confidence > 0.0


def test_icon_requires_interactive_members():
    result = InteractiveClassifierV2().classify(
        make_evidence(
            width=32,
            height=32,
            aspect_ratio=1.0,
            member_count=1,
            edge_density=0.25,
            interior_content_density=0.45,
        )
    )
    assert result.control_type == ControlType.UNKNOWN


def test_icon_requires_sufficient_interior_content():
    result = InteractiveClassifierV2().classify(
        make_evidence(
            width=32,
            height=32,
            aspect_ratio=1.0,
            member_count=2,
            edge_density=0.25,
            interior_content_density=0.29,
        )
    )
    assert result.control_type == ControlType.UNKNOWN


def test_large_panel_is_not_button():
    result = InteractiveClassifierV2().classify(
        make_evidence(
            width=500,
            height=100,
            aspect_ratio=5.0,
        )
    )
    assert result.control_type == ControlType.UNKNOWN
    assert not result.is_interactive
