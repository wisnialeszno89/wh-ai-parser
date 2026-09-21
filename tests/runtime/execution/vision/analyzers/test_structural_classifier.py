from app.runtime.execution.vision.analyzers.structural_classifier import (
    StructuralClassifier,
)
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.rect import Rect


def test_detects_horizontal_toolbar() -> None:
    classifier = StructuralClassifier()

    candidates = [
        Rect(x=0, y=0, width=900, height=100),
        Rect(x=20, y=20, width=40, height=40),
        Rect(x=80, y=20, width=40, height=40),
        Rect(x=140, y=20, width=40, height=40),
    ]

    result = classifier.classify(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert result[0].control_type == ControlType.TOOLBAR
    assert result[0].child_count == 3
    assert result[0].confidence >= 0.90


def test_detects_vertical_toolbar() -> None:
    classifier = StructuralClassifier()

    candidates = [
        Rect(x=0, y=0, width=100, height=700),
        Rect(x=20, y=20, width=40, height=40),
        Rect(x=20, y=80, width=40, height=40),
        Rect(x=20, y=140, width=40, height=40),
    ]

    result = classifier.classify(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert result[0].control_type == ControlType.TOOLBAR
    assert result[0].child_count == 3


def test_detects_large_square_canvas() -> None:
    classifier = StructuralClassifier()

    candidates = [
        Rect(x=100, y=100, width=700, height=700),
    ]

    result = classifier.classify(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert result[0].control_type == ControlType.CANVAS
    assert result[0].child_count == 0


def test_detects_panel_from_contained_candidates() -> None:
    classifier = StructuralClassifier()

    candidates = [
        Rect(x=50, y=50, width=800, height=400),
        Rect(x=100, y=100, width=200, height=100),
        Rect(x=400, y=100, width=200, height=100),
    ]

    result = classifier.classify(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert result[0].control_type == ControlType.PANEL
    assert result[0].child_count == 2


def test_detects_section_from_multiple_children() -> None:
    classifier = StructuralClassifier()

    candidates = [
        Rect(x=100, y=100, width=400, height=200),
        Rect(x=130, y=130, width=60, height=60),
        Rect(x=220, y=130, width=60, height=60),
    ]

    result = classifier.classify(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert result[0].control_type == ControlType.SECTION
    assert result[0].child_count == 2


def test_keeps_normal_candidate_unknown() -> None:
    classifier = StructuralClassifier()

    candidates = [
        Rect(x=100, y=100, width=80, height=40),
    ]

    result = classifier.classify(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert result[0].control_type == ControlType.UNKNOWN
    assert result[0].child_count == 0


def test_counts_direct_children_not_all_ancestors() -> None:
    classifier = StructuralClassifier()

    candidates = [
        Rect(x=0, y=0, width=900, height=900),      # panel
        Rect(x=100, y=100, width=600, height=600),  # section
        Rect(x=150, y=150, width=100, height=100),  # child
        Rect(x=300, y=150, width=100, height=100),  # child
    ]

    result = classifier.classify(
        candidates,
        roi_width=1000,
        roi_height=1000,
    )

    assert result[0].child_count == 1
    assert result[1].child_count == 2
