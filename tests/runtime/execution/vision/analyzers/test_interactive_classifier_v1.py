from app.runtime.execution.vision.analyzers.interactive_classifier_v1 import (
    InteractiveClassification,
    InteractiveClassifierV1,
)
from app.runtime.execution.vision.models.candidate_evidence import (
    CandidateEvidence,
)
from app.runtime.execution.vision.models.candidate_features import (
    CandidateFeatures,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.models.visual_features import (
    VisualFeatures,
)


def _evidence() -> CandidateEvidence:
    return CandidateEvidence(
        candidate=CandidateFeatures(
            width=100,
            height=30,
            area=3000,
            aspect_ratio=100 / 30,
            area_ratio=0.01,
            width_ratio=0.10,
            height_ratio=0.03,
            center_x=0.5,
            center_y=0.5,
            depth=1,
            child_count=1,
            sibling_count=3,
            touches_left=False,
            touches_right=False,
            touches_top=False,
            touches_bottom=False,
        ),
        visual=VisualFeatures(
            edge_density=0.10,
            border_edge_density=0.02,
            horizontal_edge_density=0.03,
            vertical_edge_density=0.02,
            contour_density=0.01,
            dark_pixel_ratio=0.10,
            bright_pixel_ratio=0.80,
            interior_content_density=0.15,
        ),
    )


def test_interactive_classifier_v1_has_conservative_unknown_default():
    result = InteractiveClassifierV1().classify(_evidence())

    assert isinstance(result, InteractiveClassification)
    assert result.control_type == ControlType.UNKNOWN
    assert result.confidence == 0.0
    assert result.is_interactive is False



def test_interactive_classifier_v1_detects_button_like_candidate():
    evidence = CandidateEvidence(
        candidate=CandidateFeatures(
            width=100,
            height=30,
            area=3000,
            aspect_ratio=100 / 30,
            area_ratio=0.01,
            width_ratio=0.10,
            height_ratio=0.03,
            center_x=0.5,
            center_y=0.5,
            depth=1,
            child_count=1,
            sibling_count=3,
            touches_left=False,
            touches_right=False,
            touches_top=False,
            touches_bottom=False,
        ),
        visual=VisualFeatures(
            edge_density=0.20,
            border_edge_density=0.08,
            horizontal_edge_density=0.06,
            vertical_edge_density=0.04,
            contour_density=0.01,
            dark_pixel_ratio=0.08,
            bright_pixel_ratio=0.80,
            interior_content_density=0.12,
        ),
    )

    result = InteractiveClassifierV1().classify(evidence)

    assert result.control_type == ControlType.BUTTON
    assert result.confidence >= 0.70
    assert result.is_interactive is True



def test_interactive_classifier_v1_rejects_button_without_strong_border():
    evidence = CandidateEvidence(
        candidate=CandidateFeatures(
            width=100,
            height=30,
            area=3000,
            aspect_ratio=100 / 30,
            area_ratio=0.01,
            width_ratio=0.10,
            height_ratio=0.03,
            center_x=0.5,
            center_y=0.5,
            depth=1,
            child_count=1,
            sibling_count=3,
            touches_left=False,
            touches_right=False,
            touches_top=False,
            touches_bottom=False,
        ),
        visual=VisualFeatures(
            edge_density=0.20,
            border_edge_density=0.01,
            horizontal_edge_density=0.06,
            vertical_edge_density=0.04,
            contour_density=0.01,
            dark_pixel_ratio=0.08,
            bright_pixel_ratio=0.80,
            interior_content_density=0.12,
        ),
    )

    result = InteractiveClassifierV1().classify(evidence)

    assert result.control_type == ControlType.UNKNOWN
    assert result.is_interactive is False
