from app.runtime.execution.vision.bridges.tracked_object_gui_bridge import (
    TrackedObjectGUIBridge,
)
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import TrackedObject, TrackedObjectStatus


def make_tracked(
    bounds: Rect,
    track_id: str = "TO-0001",
) -> TrackedObject:
    logical_object = LogicalObject(
        bounds=bounds,
        root_contour_index=0,
        member_contour_indices=(0,),
    )

    return TrackedObject(
        id=track_id,
        object=logical_object,
        control_type=ControlType.BUTTON,
        confidence=0.91,
    )


def test_resolves_existing_gui_object_by_geometry() -> None:
    target = GUIObject(
        id="button_1",
        type=ControlType.BUTTON,
        bounds=Rect(x=100, y=50, width=80, height=30),
    )

    root = GUIObject(
        id="window",
        type=ControlType.WINDOW,
        bounds=Rect(x=0, y=0, width=800, height=600),
        children=[target],
    )

    tracked = make_tracked(
        Rect(x=100, y=50, width=80, height=30)
    )

    bridge = TrackedObjectGUIBridge()

    resolved = bridge.resolve(tracked, root)

    assert resolved is target
    assert resolved.id == "button_1"


def test_resolves_nested_gui_object() -> None:
    target = GUIObject(
        id="nested_button",
        type=ControlType.BUTTON,
        bounds=Rect(x=200, y=120, width=90, height=35),
    )

    panel = GUIObject(
        id="panel",
        type=ControlType.PANEL,
        bounds=Rect(x=150, y=80, width=300, height=200),
        children=[target],
    )

    root = GUIObject(
        id="window",
        type=ControlType.WINDOW,
        bounds=Rect(x=0, y=0, width=800, height=600),
        children=[panel],
    )

    tracked = make_tracked(
        Rect(x=200, y=120, width=90, height=35)
    )

    resolved = TrackedObjectGUIBridge().resolve(tracked, root)

    assert resolved is target


def test_rejects_unrelated_gui_object() -> None:
    target = GUIObject(
        id="other_button",
        type=ControlType.BUTTON,
        bounds=Rect(x=500, y=400, width=80, height=30),
    )

    root = GUIObject(
        id="window",
        type=ControlType.WINDOW,
        bounds=Rect(x=0, y=0, width=800, height=600),
        children=[target],
    )

    tracked = make_tracked(
        Rect(x=100, y=50, width=80, height=30)
    )

    resolved = TrackedObjectGUIBridge().resolve(tracked, root)

    assert resolved is None


def test_does_not_mutate_gui_object() -> None:
    target = GUIObject(
        id="button_1",
        type=ControlType.BUTTON,
        bounds=Rect(x=100, y=50, width=80, height=30),
        confidence=0.42,
    )

    root = GUIObject(
        id="window",
        type=ControlType.WINDOW,
        bounds=Rect(x=0, y=0, width=800, height=600),
        children=[target],
    )

    tracked = make_tracked(
        Rect(x=100, y=50, width=80, height=30)
    )

    bridge = TrackedObjectGUIBridge()

    resolved = bridge.resolve(tracked, root)

    assert resolved is target
    assert target.confidence == 0.42
    assert target.type == ControlType.BUTTON



def test_does_not_resolve_lost_track() -> None:
    target = GUIObject(
        id="button_1",
        type=ControlType.BUTTON,
        bounds=Rect(x=100, y=50, width=80, height=30),
    )

    root = GUIObject(
        id="window",
        type=ControlType.WINDOW,
        bounds=Rect(x=0, y=0, width=800, height=600),
        children=[target],
    )

    tracked = make_tracked(
        Rect(x=100, y=50, width=80, height=30)
    )

    tracked.status = TrackedObjectStatus.LOST

    resolved = TrackedObjectGUIBridge().resolve(
        tracked,
        root,
    )

    assert resolved is None
