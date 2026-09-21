from app.runtime.execution.vision.analyzers.candidate_object_grouper_v1 import (
    CandidateObjectGrouperV1,
)
from app.runtime.execution.vision.analyzers.visual_feature_extractor import (
    VisualFeatureExtractor,
)
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.logical_object_evidence import (
    LogicalObjectEvidence,
)


class LogicalObjectEvidenceExtractor:
    """
    Extract measurable evidence from a reconstructed LogicalObject.

    Semantic interpretation is deliberately left to later classifiers.
    """

    def __init__(
        self,
        visual_feature_extractor: VisualFeatureExtractor | None = None,
    ) -> None:
        self.visual_feature_extractor = (
            visual_feature_extractor or VisualFeatureExtractor()
        )

    def extract(
        self,
        image,
        logical_object: LogicalObject,
        *,
        roi_width: int,
        roi_height: int,
        contours=None,
        child_count: int = 0,
    ) -> LogicalObjectEvidence:
        rect = logical_object.bounds

        visual = self.visual_feature_extractor.extract(
            image,
            rect,
            contours=contours,
        )

        area = rect.area

        aspect_ratio = (
            rect.width / float(rect.height)
            if rect.height > 0
            else 0.0
        )

        roi_area = roi_width * roi_height

        area_ratio = (
            area / float(roi_area)
            if roi_area > 0
            else 0.0
        )

        return LogicalObjectEvidence(
            width=rect.width,
            height=rect.height,
            area=area,
            aspect_ratio=aspect_ratio,
            area_ratio=area_ratio,
            member_count=logical_object.member_count,
            child_count=child_count,
            visual=visual,
        )
