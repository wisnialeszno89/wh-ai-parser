from dataclasses import dataclass

from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)
from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)
from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)
from app.agent.environment.windowhub_focus_window_preparation_handler import (
    WindowHubFocusWindowPreparationHandler,
)


@dataclass
class FakeWindow:
    _hWnd: int = 1234
    title: str = "Okna - TEST"
    isMinimized: bool = False

    def __post_init__(self):
        self.restore_called = False
        self.activate_called = False

    def restore(self):
        self.restore_called = True
        self.isMinimized = False

    def activate(self):
        self.activate_called = True


def _preparation():
    return EnvironmentPreparation(
        preparation_type=EnvironmentPreparationType.PREPARE,
        strategy=EnvironmentPreparationStrategy.FOCUS_WINDOW,
        target_application="WindowHub",
        reason="Focus required",
    )


def test_focus_handler_activates_and_verifies_window():
    window = FakeWindow()
    handler = WindowHubFocusWindowPreparationHandler(
        window_provider=lambda: window,
        foreground_provider=lambda: 1234,
        sleep_seconds=0,
    )

    result = handler.execute(_preparation())

    assert result.success is True
    assert window.activate_called is True
    assert result.metadata["focused"] is True
    assert result.metadata["window_handle"] == 1234


def test_focus_handler_fails_when_foreground_does_not_match():
    window = FakeWindow()
    handler = WindowHubFocusWindowPreparationHandler(
        window_provider=lambda: window,
        foreground_provider=lambda: 9999,
        sleep_seconds=0,
    )

    result = handler.execute(_preparation())

    assert result.success is False
    assert result.metadata["focused"] is False
    assert result.metadata["foreground_handle"] == 9999


def test_focus_handler_restores_minimized_window():
    window = FakeWindow(isMinimized=True)
    handler = WindowHubFocusWindowPreparationHandler(
        window_provider=lambda: window,
        foreground_provider=lambda: 1234,
        sleep_seconds=0,
    )

    result = handler.execute(_preparation())

    assert result.success is True
    assert window.restore_called is True
    assert window.activate_called is True
