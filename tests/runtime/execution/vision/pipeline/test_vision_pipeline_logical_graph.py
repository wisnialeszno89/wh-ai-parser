from types import SimpleNamespace

import numpy as np

from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.pipeline.vision_pipeline import VisionPipeline
from app.runtime.execution.window.window_rect import WindowRect
from app.wh.vision.screenshot import Screenshot


def make_logical_object(
    x: int,
    y: int,
    width: int,
    height: int,
    root: int,
) -> LogicalObject:
    return LogicalObject(
        bounds=Rect(
            x=x,
            y=y,
            width=width,
            height=height,
        ),
        root_contour_index=root,
        member_contour_indices=(root,),
    )


def test_pipeline_publishes_logical_objects_and_graph(monkeypatch) -> None:
    pipeline = VisionPipeline()

    window = WindowRect(
        left=10,
        top=20,
        width=800,
        height=600,
    )
    screenshot = Screenshot(
        width=800,
        height=600,
        image=np.zeros((600, 800, 3), dtype=np.uint8),
    )

    toolbar = SimpleNamespace(
        children=[
            SimpleNamespace(
                id="section-1",
                bounds=Rect(
                    x=0,
                    y=0,
                    width=300,
                    height=100,
                ),
                children=[],
            )
        ]
    )

    logical_objects = [
        make_logical_object(10, 10, 100, 50, 1),
        make_logical_object(20, 20, 30, 20, 2),
    ]

    monkeypatch.setattr(
        pipeline.window_locator,
        "locate",
        lambda: window,
    )
    monkeypatch.setattr(
        pipeline.screenshot_engine,
        "capture",
        lambda _: screenshot,
    )
    monkeypatch.setattr(
        pipeline.toolbar_detector,
        "analyze",
        lambda _: toolbar,
    )
    monkeypatch.setattr(
        pipeline.canvas_analyzer,
        "analyze",
        lambda context: context,
    )
    monkeypatch.setattr(
        pipeline.construction_analyzer,
        "analyze",
        lambda _: None,
    )
    monkeypatch.setattr(
        pipeline.section_analyzer,
        "analyze",
        lambda *_: None,
    )
    monkeypatch.setattr(
        pipeline.control_detector,
        "analyze",
        lambda *_: setattr(
            pipeline.control_detector,
            "last_logical_objects",
            logical_objects,
        ),
    )
    monkeypatch.setattr(
        pipeline.roi_extractor,
        "extract",
        lambda *_: None,
    )
    monkeypatch.setattr(
        pipeline.roi_debug,
        "save",
        lambda *_: None,
    )
    monkeypatch.setattr(
        pipeline.scene_graph_builder,
        "build",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        pipeline.debug_overlay,
        "render",
        lambda **_: None,
    )

    context = pipeline.observe()

    assert context.logical_objects == logical_objects
    assert context.logical_object_graph is not None
    assert len(context.logical_object_graph.objects) == 2

    relationships = context.logical_object_graph.relationships

    assert len(relationships) == 1
    assert relationships[0].source_id == "LO-0001"
    assert relationships[0].target_id == "LO-0002"



def test_vision_pipeline_preserves_track_identity_between_observations(
    monkeypatch,
) -> None:
    pipeline = VisionPipeline()

    window = WindowRect(
        left=10,
        top=20,
        width=800,
        height=600,
    )

    screenshot = Screenshot(
        width=800,
        height=600,
        image=np.zeros((600, 800, 3), dtype=np.uint8),
    )

    toolbar = SimpleNamespace(
        children=[
            SimpleNamespace(
                id="section-1",
                bounds=Rect(
                    x=0,
                    y=0,
                    width=300,
                    height=100,
                ),
                children=[],
            )
        ]
    )

    logical_object = make_logical_object(
        x=100,
        y=100,
        width=20,
        height=20,
        root=1,
    )

    monkeypatch.setattr(
        pipeline.window_locator,
        "locate",
        lambda: window,
    )

    monkeypatch.setattr(
        pipeline.screenshot_engine,
        "capture",
        lambda _: screenshot,
    )

    monkeypatch.setattr(
        pipeline.toolbar_detector,
        "analyze",
        lambda _: toolbar,
    )

    monkeypatch.setattr(
        pipeline.canvas_analyzer,
        "analyze",
        lambda context: context,
    )

    monkeypatch.setattr(
        pipeline.construction_analyzer,
        "analyze",
        lambda _: None,
    )

    monkeypatch.setattr(
        pipeline.section_analyzer,
        "analyze",
        lambda *_: None,
    )

    monkeypatch.setattr(
        pipeline.control_detector,
        "analyze",
        lambda *_: setattr(
            pipeline.control_detector,
            "last_logical_objects",
            [logical_object],
        ),
    )

    monkeypatch.setattr(
        pipeline.roi_extractor,
        "extract",
        lambda *_: None,
    )

    monkeypatch.setattr(
        pipeline.roi_debug,
        "save",
        lambda *_: None,
    )

    monkeypatch.setattr(
        pipeline.scene_graph_builder,
        "build",
        lambda *_args, **_kwargs: None,
    )

    monkeypatch.setattr(
        pipeline.debug_overlay,
        "render",
        lambda **_: None,
    )

    first = pipeline.observe()

    first_track_id = first.tracked_objects[0].id
    first_observation_count = first.tracked_objects[0].observation_count

    second = pipeline.observe()

    assert len(first.tracked_objects) == 1
    assert len(second.tracked_objects) == 1

    assert first_track_id == "TO-0001"
    assert second.tracked_objects[0].id == "TO-0001"

    assert first_observation_count == 1
    assert second.tracked_objects[0].observation_count == 2

    assert second.tracked_objects[0].status.value == "stable"
