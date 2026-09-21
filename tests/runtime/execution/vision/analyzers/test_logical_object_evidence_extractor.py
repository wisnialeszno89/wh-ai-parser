import numpy as np

from app.runtime.execution.vision.analyzers.logical_object_evidence_extractor import (
    LogicalObjectEvidenceExtractor,
)
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect


def test_extracts_logical_object_geometry():
    image = np.full(
        (100, 200, 3),
        255,
        dtype=np.uint8,
    )

    logical_object = LogicalObject(
        bounds=Rect(20, 30, 60, 20),
        root_contour_index=10,
        member_contour_indices=(10, 11),
    )

    evidence = LogicalObjectEvidenceExtractor().extract(
        image,
        logical_object,
        roi_width=200,
        roi_height=100,
        child_count=1,
    )

    assert evidence.width == 60
    assert evidence.height == 20
    assert evidence.area == 1200
    assert evidence.aspect_ratio == 3.0
    assert evidence.area_ratio == 0.06

    assert evidence.member_count == 2
    assert evidence.child_count == 1


def test_handles_zero_height_without_division_error():
    image = np.full(
        (100, 200, 3),
        255,
        dtype=np.uint8,
    )

    logical_object = LogicalObject(
        bounds=Rect(20, 30, 60, 0),
        root_contour_index=10,
        member_contour_indices=(10,),
    )

    evidence = LogicalObjectEvidenceExtractor().extract(
        image,
        logical_object,
        roi_width=200,
        roi_height=100,
    )

    assert evidence.aspect_ratio == 0.0
