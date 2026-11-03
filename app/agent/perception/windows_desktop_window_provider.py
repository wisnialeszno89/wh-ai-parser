"""Perceive the bounded inventory of visible top-level Windows windows."""

from __future__ import annotations

from collections import Counter

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.windows_desktop_environment_adapter import (
    DesktopWindowSnapshot,
)
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.perception_provider import PerceptionProvider
from app.agent.perception.screen_element import ScreenElement


class WindowsDesktopWindowProvider(PerceptionProvider):
    """Expose open desktop windows as semantic, non-clickable scene entities.

    Native HWND values stay in local ScreenElement metadata. The V2 world
    projection removes them before sending the scene to NaviMind.
    """

    MAX_WINDOWS = 64

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        raw_windows = observation.metadata.get("desktop_windows", ())
        if not isinstance(raw_windows, (tuple, list)):
            return ()

        foreground_handle = observation.metadata.get(
            "foreground_window_handle",
            observation.metadata.get("window_handle"),
        )
        try:
            foreground_handle = int(foreground_handle)
        except (TypeError, ValueError, OverflowError):
            foreground_handle = 0

        candidates = [
            item
            for item in raw_windows[: self.MAX_WINDOWS]
            if isinstance(item, DesktopWindowSnapshot)
            and isinstance(item.handle, int)
            and not isinstance(item.handle, bool)
            and item.handle > 0
            and item.is_visible is True
            and item.rect is not None
            and int(item.rect.width) > 0
            and int(item.rect.height) > 0
        ]

        base_labels: list[str] = []
        for item in candidates:
            title = (
                item.title.strip()
                if isinstance(item.title, str) and item.title.strip()
                else "<BRAK TYTUŁU>"
            )
            application = (
                item.application.strip()
                if isinstance(item.application, str) and item.application.strip()
                else "unknown application"
            )
            base_labels.append(f"{title} — {application}")

        totals = Counter(base_labels)
        seen: Counter[str] = Counter()
        elements: list[ScreenElement] = []

        for item, base_label in zip(candidates, base_labels):
            seen[base_label] += 1
            label = base_label
            if totals[base_label] > 1:
                label = f"{base_label} (window {seen[base_label]})"

            is_foreground = (
                item.handle == foreground_handle
                or item.is_foreground is True
            )
            elements.append(
                ScreenElement(
                    kind="application_window",
                    label=label[:1_000],
                    x=int(item.rect.left),
                    y=int(item.rect.top),
                    width=int(item.rect.width),
                    height=int(item.rect.height),
                    confidence=0.99,
                    metadata={
                        "source": "windows_desktop_window",
                        "provider_family": "windows_desktop",
                        "window_handle": item.handle,
                        "window_title": item.title,
                        "process_name": item.application,
                        "is_foreground": is_foreground,
                        "is_minimized": bool(item.is_minimized),
                        "is_visible": bool(item.is_visible),
                        "is_root_window": (
                            item.root_owner_handle == item.handle
                        ),
                        "window_area": (
                            int(item.rect.width) * int(item.rect.height)
                        ),
                    },
                    interaction_capability=InteractionCapability.UNKNOWN,
                )
            )

        return tuple(elements)
