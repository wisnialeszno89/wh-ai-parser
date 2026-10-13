from __future__ import annotations

from app.agent.adapters.browser_adapter import BrowserAdapter
from app.agent.environment.environment_adapter import EnvironmentAdapter
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import EnvironmentState


class BrowserEnvironmentAdapter(EnvironmentAdapter):
    """
    Minimal environment adapter for Browser mode.

    Browser-specific state remains in BrowserPage. The generic environment
    observation only supplies the shared control-loop lifecycle with a
    provider-neutral application/window identity.
    """

    def __init__(self, browser_adapter: BrowserAdapter) -> None:
        if not isinstance(browser_adapter, BrowserAdapter):
            raise TypeError(
                "BrowserEnvironmentAdapter requires BrowserAdapter."
            )

        self.browser_adapter = browser_adapter

    def observe(self) -> EnvironmentObservation:
        page = self.browser_adapter.read()

        return EnvironmentObservation(
            state=EnvironmentState(
                active_application="Browser",
                active_window_title=page.title,
            ),
            metadata={
                "browser_page": page,
            },
        )
