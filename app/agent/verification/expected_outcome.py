from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedOutcome:
    """
    Describes what the agent expects to observe after
    executing an action.

    The model intentionally remains environment-independent.
    Verification is performed against the semantic scene
    and environment observation.
    """

    description: str

    expected_element_label: str | None = None

    expected_element_kind: str | None = None

    element_should_exist: bool = True

    expected_active_application: str | None = None

    expected_window_title: str | None = None
