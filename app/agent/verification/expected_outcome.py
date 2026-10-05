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

    expected_element_current_value: str | None = None

    expected_active_application: str | None = None

    expected_window_title: str | None = None

    # When enabled, verification requires the post-action semantic
    # scene to differ from the scene observed immediately before
    # execution. The baseline is captured by ExpectationResolver.
    require_scene_change: bool = False

    baseline_scene_signature: tuple[tuple[object, ...], ...] | None = None
