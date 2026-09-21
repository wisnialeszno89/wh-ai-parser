from __future__ import annotations

import cv2

from app.runtime.execution.vision.analyzers.candidate_features import (
    CandidateFeatureExtractor,
)
from app.runtime.execution.vision.analyzers.candidate_hierarchy import (
    CandidateHierarchy,
    CandidateNode,
)
from app.runtime.execution.vision.analyzers.candidate_filter import (
    CandidateFilter,
)
from app.runtime.execution.vision.analyzers.structural_classifier_v2 import (
    StructuralClassifierV2,
    StructuralClassificationV2,
)
from app.runtime.execution.vision.analyzers.visual_feature_extractor import (
    VisualFeatureExtractor,
)
from app.runtime.execution.vision.models.candidate_evidence import CandidateEvidence
from app.runtime.execution.vision.models.control_role import (
    ControlRole,
)
from app.runtime.execution.vision.models.control_state import (
    ControlState,
)
from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)
from app.wh.vision.screenshot import (
    Screenshot,
)


class ControlDetector:
    """
    Detects and structurally organizes potential GUI controls.

    Detection pipeline:

        screenshot
            ↓
        contours
            ↓
        CandidateFilter
            ↓
        VisionCandidate[]
            ↓
        CandidateFeatureExtractor
            ↓
        CandidateFeatures[]
            ↓
        StructuralClassifierV2
            ↓
        CandidateHierarchy
            ↓
        GUIObject tree
    """

    CANNY_LOW = 60
    CANNY_HIGH = 150

    def __init__(
        self,
        candidate_filter: CandidateFilter | None = None,
        feature_extractor: CandidateFeatureExtractor | None = None,
        structural_classifier: StructuralClassifierV2 | None = None,
        candidate_hierarchy: CandidateHierarchy | None = None,
        visual_feature_extractor: VisualFeatureExtractor | None = None,
    ) -> None:
        self.candidate_filter = (
            candidate_filter
            or CandidateFilter()
        )

        self.feature_extractor = (
            feature_extractor
            or CandidateFeatureExtractor()
        )

        self.structural_classifier = (
            structural_classifier
            or StructuralClassifierV2()
        )

        self.candidate_hierarchy = (
            candidate_hierarchy
            or CandidateHierarchy()
        )

        self.visual_feature_extractor = (
            visual_feature_extractor
            or VisualFeatureExtractor()
        )

    def analyze(
        self,
        screenshot: Screenshot,
        section: GUIObject,
    ) -> None:
        if section.bounds is None:
            section.children.clear()
            return

        image = screenshot.image
        r = section.bounds

        roi = image[
            r.top:r.bottom,
            r.left:r.right,
        ]

        if roi.size == 0:
            section.children.clear()
            return

        gray = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2GRAY,
        )

        edges = cv2.Canny(
            gray,
            self.CANNY_LOW,
            self.CANNY_HIGH,
        )

        contours, hierarchy = cv2.findContours(
            edges,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        candidates = self.candidate_filter.filter(
            contours,
            hierarchy=hierarchy,
            roi_width=roi.shape[1],
            roi_height=roi.shape[0],
        )

        section.children.clear()

        if not candidates:
            return

        features = self.feature_extractor.extract(
            candidates,
            roi_width=roi.shape[1],
            roi_height=roi.shape[0],
        )

        classifications = self.structural_classifier.classify(
            features,
        )

        evidence_by_contour = {
            candidate.contour_index: CandidateEvidence(
                candidate=feature,
                visual=self.visual_feature_extractor.extract(
                    roi,
                    candidate.rect,
                    contours=contours,
                ),
            )
            for candidate, feature in zip(candidates, features)
        }

        classifications_by_contour = {
            candidate.contour_index: classification
            for candidate, classification in zip(
                candidates,
                classifications,
            )
        }

        hierarchy_tree = self.candidate_hierarchy.build(
            candidates,
        )

        for root in hierarchy_tree:
            section.add_child(
                self._build_gui_object(
                    root,
                    classifications_by_contour,
                    evidence_by_contour,
                    section,
                    r.left,
                    r.top,
                )
            )

    def _build_gui_object(
        self,
        node: CandidateNode,
        classifications_by_contour: dict[
            int,
            StructuralClassificationV2,
        ],
        evidence_by_contour: dict[int, CandidateEvidence],
        section: GUIObject,
        offset_x: int,
        offset_y: int,
    ) -> GUIObject:
        candidate = node.candidate

        classification = classifications_by_contour[
            candidate.contour_index
        ]

        evidence = evidence_by_contour[
            candidate.contour_index
        ]

        control = GUIObject(
            id=(
                f"{section.id}"
                f"_candidate_{candidate.contour_index}"
            ),
            type=classification.control_type,
            role=ControlRole.UNKNOWN,
            state=ControlState.VISIBLE,
            bounds=candidate.rect.translate(
                offset_x,
                offset_y,
            ),
            confidence=classification.confidence,
            evidence=evidence,
        )

        for child_node in node.children:
            control.add_child(
                self._build_gui_object(
                    child_node,
                    classifications_by_contour,
                    evidence_by_contour,
                    section,
                    offset_x,
                    offset_y,
                )
            )

        return control
