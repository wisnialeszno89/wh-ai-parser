from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentState:
    """
    Basic state describing the environment currently
    visible to the agent.

    This model intentionally remains platform-neutral.

    It can represent:
    - a fake test environment
    - Windows
    - a browser
    - WH
    - another desktop application
    """

    active_application: str | None = None

    active_window_title: str | None = None

    screen_width: int | None = None

    screen_height: int | None = None
