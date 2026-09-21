import cv2

from app.runtime.execution.vision.models.control_role import ControlRole
from app.runtime.execution.vision.models.control_state import ControlState
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.scene_graph_builder import SceneGraphBuilder
from app.wh.vision.screenshot import Screenshot


def test_scene_graph_builder_attaches_toolbar_to_window():
    image = cv2.imread("tests/data/screenshot.png")

    assert image is not None

    height, width = image.shape[:2]

    screenshot = Screenshot(
        width=width,
        height=height,
        image=image,
    )

    button = GUIObject(
        id="candidate_46",
        type=ControlType.BUTTON,
        role=ControlRole.UNKNOWN,
        state=ControlState.VISIBLE,
        bounds=Rect(
            x=47,
            y=192,
            width=52,
            height=17,
        ),
        confidence=0.75,
    )

    toolbar = GUIObject(
        id="toolbar",
        type=ControlType.TOOLBAR,
        role=ControlRole.UNKNOWN,
        state=ControlState.VISIBLE,
        bounds=Rect(
            x=0,
            y=0,
            width=width,
            height=height,
        ),
    )

    toolbar.add_child(button)

    graph = SceneGraphBuilder().build(
        screenshot,
        toolbar=toolbar,
    )

    assert graph.root.type == ControlType.WINDOW
    assert graph.root.bounds is not None
    assert graph.root.bounds.width == width
    assert graph.root.bounds.height == height

    assert graph.root.children == [toolbar]
    assert toolbar.children == [button]

    assert list(graph.walk()) == [
        graph.root,
        toolbar,
        button,
    ]