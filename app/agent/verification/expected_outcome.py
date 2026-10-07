from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedOutcome:
    """
    Describes what the agent expects to observe after
    executing an action.

    The model intentionally remains environment-independent.
    Verification is performed against the semantic scene,
    environment observation, or a provider-neutral application
    snapshot supplied by the execution context.
    """

    description: str

    expected_element_label: str | None = None
    expected_element_kind: str | None = None
    element_should_exist: bool = True
    expected_element_current_value: str | None = None

    expected_active_application: str | None = None
    expected_window_title: str | None = None

    # Browser/provider-neutral application state.
    expected_browser_url: str | None = None
    expected_browser_title: str | None = None
    expected_browser_element_label: str | None = None
    expected_browser_element_current_value: str | None = None

    # Optional semantic state requirements. Each mapping describes one
    # element that should be present after execution.
    expected_semantic_elements: tuple[dict[str, object], ...] = ()

    # When enabled, verification requires the post-action semantic
    # scene to differ from the scene observed immediately before
    # execution. The baseline is captured by ExpectationResolver.
    require_scene_change: bool = False

    baseline_scene_signature: tuple[tuple[object, ...], ...] | None = None

    # Browser change verification used for actions such as click/back when
    # no stronger action-specific postcondition is available.
    require_browser_change: bool = False
    baseline_browser_signature: tuple[object, ...] | None = None
