"""Application-neutral Windows UI Automation perception provider."""

from dataclasses import replace

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)


class WindowsUIAutomationProvider(WindowHubUIAutomationProvider):
    """Reuse the established UIA traversal for any observed foreground app.

    The underlying traversal is application-neutral; the Windows desktop
    adapter supplies the active HWND and window geometry. This public provider
    uses a generic provenance label so action policies do not imply WindowHub
    is the only supported application.
    """

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        elements = super().perceive(observation)
        normalized = []
        for element in elements:
            metadata = dict(element.metadata or {})
            if metadata.get("source") == "windowhub_ui_automation":
                metadata["source"] = "windows_ui_automation"
                metadata["provider_family"] = "windows_desktop"
            normalized.append(
                replace(
                    element,
                    metadata=metadata,
                )
            )
        return tuple(normalized)
