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

    # Optional provider-neutral state assertion for a uniquely identified
    # semantic element (for example uia_selected or uia_enabled).
    expected_element_state_name: str | None = None

    expected_element_state_value: object | None = None

    # Local-only UIA identity used to verify the exact control when labels repeat.
    expected_element_uia_runtime_id: str | None = None

    expected_element_automation_id: str | None = None
