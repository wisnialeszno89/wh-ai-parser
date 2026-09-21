import cv2

from app.runtime.execution.vision.analyzers.control_detector import (
    ControlDetector,
)
from app.runtime.execution.vision.models.control_role import (
    ControlRole,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)
from app.runtime.execution.vision.models.rect import (
    Rect,
)
from app.wh.vision.screenshot import (
    Screenshot,
)


def test_control_detector_creates_structurally_classified_candidates():
    image = cv2.imread(
        "tests/data/screenshot.png"
    )

    assert image is not None

    height, width = image.shape[:2]

    screenshot = Screenshot(
        width=width,
        height=height,
        image=image,
    )

    section = GUIObject(
        id="test_section",
        type=ControlType.SECTION,
        role=ControlRole.UNKNOWN,
        bounds=Rect(
            x=0,
            y=0,
            width=width,
            height=height,
        ),
    )

    detector = ControlDetector()

    detector.analyze(
        screenshot,
        section,
    )

    assert section.children

    allowed_types = {
        ControlType.UNKNOWN,
        ControlType.TOOLBAR,
        ControlType.PANEL,
        ControlType.SECTION,
        ControlType.GROUP,
        ControlType.CANVAS,
    }

    for child in section.children:
        assert child.type in allowed_types
        assert child.bounds is not None
        assert child.confidence > 0.0
        assert child.role == ControlRole.UNKNOWN


def test_control_detector_preserves_absolute_coordinates():
    image = cv2.imread(
        "tests/data/screenshot.png"
    )

    assert image is not None

    height, width = image.shape[:2]

    screenshot = Screenshot(
        width=width,
        height=height,
        image=image,
    )

    section = GUIObject(
        id="offset_section",
        type=ControlType.SECTION,
        role=ControlRole.UNKNOWN,
        bounds=Rect(
            x=100,
            y=50,
            width=min(500, width - 100),
            height=min(400, height - 50),
        ),
    )

    detector = ControlDetector()

    detector.analyze(
        screenshot,
        section,
    )

    assert section.children

    for child in section.children:
        assert child.bounds is not None

        assert child.bounds.left >= section.bounds.left
        assert child.bounds.top >= section.bounds.top
        assert child.bounds.right <= section.bounds.right
        assert child.bounds.bottom <= section.bounds.bottom


def test_control_detector_preserves_candidate_evidence():
    image = cv2.imread(
        "tests/data/screenshot.png"
    )

    assert image is not None

    height, width = image.shape[:2]

    screenshot = Screenshot(
        width=width,
        height=height,
        image=image,
    )

    section = GUIObject(
        id="evidence_section",
        type=ControlType.SECTION,
        role=ControlRole.UNKNOWN,
        bounds=Rect(
            x=0,
            y=0,
            width=width,
            height=height,
        ),
    )

    detector = ControlDetector()

    detector.analyze(
        screenshot,
        section,
    )

    assert section.children

    for child in section.children:
        assert child.evidence is not None
        assert child.evidence.candidate is not None
        assert child.evidence.visual is not None

        candidate = child.evidence.candidate

        assert candidate.width == child.bounds.width
        assert candidate.height == child.bounds.height
        assert candidate.area == child.bounds.width * child.bounds.height


class _AlwaysButtonClassifier:
    def classify(self, evidence):
        from app.runtime.execution.vision.analyzers.interactive_classifier_v1 import (
            InteractiveClassification,
        )

        return InteractiveClassification(
            control_type=ControlType.BUTTON,
            confidence=0.75,
        )


def test_control_detector_promotes_interactive_classification_to_gui_object():
    image = cv2.imread(
        "tests/data/screenshot.png"
    )

    assert image is not None

    height, width = image.shape[:2]

    screenshot = Screenshot(
        width=width,
        height=height,
        image=image,
    )

    section = GUIObject(
        id="interactive_section",
        type=ControlType.SECTION,
        role=ControlRole.UNKNOWN,
        bounds=Rect(
            x=0,
            y=0,
            width=width,
            height=height,
        ),
    )

    detector = ControlDetector(
        interactive_classifier=_AlwaysButtonClassifier(),
    )

    detector.analyze(
        screenshot,
        section,
    )

    assert section.children

    for child in section.children:
        assert child.type == ControlType.BUTTON
        assert child.confidence == 0.75
        assert child.role == ControlRole.UNKNOWN
        assert child.evidence is not None
