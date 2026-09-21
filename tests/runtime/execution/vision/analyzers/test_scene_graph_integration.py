import cv2

from app.runtime.execution.vision.analyzers.control_detector import (
    ControlDetector,
)
from app.runtime.execution.vision.analyzers.legacy_toolbar_band_detector import (
    LegacyToolbarBandDetector,
)
from app.runtime.execution.vision.analyzers.section_analyzer import (
    SectionAnalyzer,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.models.scene_graph_builder import (
    SceneGraphBuilder,
)
from app.wh.vision.screenshot import Screenshot


def test_scene_graph_is_built_from_real_screenshot():
    image = cv2.imread("tests/data/screenshot.png")

    assert image is not None

    height, width = image.shape[:2]

    screenshot = Screenshot(
        width=width,
        height=height,
        image=image,
    )

    toolbar = LegacyToolbarBandDetector().analyze(
        screenshot,
    )

    assert toolbar is not None
    assert toolbar.type == ControlType.TOOLBAR

    SectionAnalyzer().analyze(
        screenshot,
        toolbar,
    )

    assert toolbar.children

    detector = ControlDetector()

    for section in toolbar.children:
        detector.analyze(
            screenshot,
            section,
        )

    graph = SceneGraphBuilder().build(
        screenshot,
        toolbar=toolbar,
    )

    assert graph.root.type == ControlType.WINDOW
    assert graph.root.children == [toolbar]

    nodes = list(graph.walk())

    assert nodes[0] is graph.root
    assert nodes[1] is toolbar

    section_nodes = [
        node
        for node in nodes
        if node.type == ControlType.SECTION
    ]

    assert section_nodes

    control_nodes = [
        node
        for node in nodes
        if node.type != ControlType.WINDOW
        and node.type != ControlType.TOOLBAR
        and node.type != ControlType.SECTION
    ]

    assert control_nodes
