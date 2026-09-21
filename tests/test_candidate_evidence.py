from app.runtime.execution.vision.models.candidate_evidence import (
    CandidateEvidence,
)
from app.runtime.execution.vision.models.candidate_features import (
    CandidateFeatures,
)
from app.runtime.execution.vision.models.visual_features import (
    VisualFeatures,
)


def test_candidate_evidence_combines_candidate_and_visual_features():
    candidate = CandidateFeatures(
        width=100,
        height=40,
        area=4000,
        aspect_ratio=2.5,
        area_ratio=0.05,
        width_ratio=0.2,
        height_ratio=0.1,
        center_x=0.5,
        center_y=0.5,
        depth=1,
        child_count=2,
        sibling_count=3,
        touches_left=False,
        touches_right=False,
        touches_top=False,
        touches_bottom=False,
    )

    visual = VisualFeatures(
        edge_density=0.12,
        contour_density=0.004,
        dark_pixel_ratio=0.2,
        bright_pixel_ratio=0.7,
    )

    evidence = CandidateEvidence(
        candidate=candidate,
        visual=visual,
    )

    assert evidence.candidate is candidate
    assert evidence.visual is visual
