from types import SimpleNamespace

from app.runtime.execution.interactions.executors.click_executor import (
    ClickExecutor,
)
from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)
from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)
from app.runtime.execution.vision.models.rect import (
    Rect,
)


class FakeMouse:

    def __init__(self):
        self.clicks = []

    def click(self, x, y):
        self.clicks.append((x, y))


class FakeVisualTarget:

    def __init__(self, bounds):
        self.id = "vision_button_745"
        self.bounds = bounds


def make_context(left=100, top=200):
    return SimpleNamespace(
        window=SimpleNamespace(
            left=left,
            top=top,
        )
    )


def test_click_executor_translates_local_coordinates_to_screen():
    mouse = FakeMouse()

    executor = ClickExecutor(
        mouse=mouse,
    )

    target = FakeVisualTarget(
        bounds=Rect(
            x=47,
            y=192,
            width=56,
            height=21,
        ),
    )

    step = InteractionStep(
        action=InteractionAction.CLICK,
        visual_target=target,
    )

    context = make_context(
        left=100,
        top=200,
    )

    result = executor.execute(
        context,
        step,
    )

    assert result.success is True
    assert mouse.clicks == [
        (175, 402),
    ]


def test_click_executor_requires_visual_target():
    mouse = FakeMouse()

    executor = ClickExecutor(
        mouse=mouse,
    )

    step = InteractionStep(
        action=InteractionAction.CLICK,
        visual_target=None,
    )

    context = make_context()

    result = executor.execute(
        context,
        step,
    )

    assert result.success is False
    assert result.message == "CLICK requires a visual_target."
    assert mouse.clicks == []


def test_click_executor_requires_target_bounds():
    mouse = FakeMouse()

    executor = ClickExecutor(
        mouse=mouse,
    )

    target = FakeVisualTarget(
        bounds=None,
    )

    step = InteractionStep(
        action=InteractionAction.CLICK,
        visual_target=target,
    )

    context = make_context()

    result = executor.execute(
        context,
        step,
    )

    assert result.success is False
    assert result.message == "CLICK visual_target has no bounds."
    assert mouse.clicks == []


def test_click_executor_requires_window_origin():
    mouse = FakeMouse()

    executor = ClickExecutor(
        mouse=mouse,
    )

    target = FakeVisualTarget(
        bounds=Rect(
            x=47,
            y=192,
            width=56,
            height=21,
        ),
    )

    step = InteractionStep(
        action=InteractionAction.CLICK,
        visual_target=target,
    )

    context = SimpleNamespace(
        window=None,
    )

    result = executor.execute(
        context,
        step,
    )

    assert result.success is False
    assert result.message == "CLICK requires window origin."
    assert mouse.clicks == []
