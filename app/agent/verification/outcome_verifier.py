from app.agent.perception.screen_scene import (
    ScreenScene,
)

from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)

from app.agent.verification.verification_result import (
    VerificationResult,
)


class OutcomeVerifier:
    """
    Verifies whether the perceived environment matches
    an expected outcome after an action.

    Current verification rules are intentionally simple
    and deterministic.

    Supported checks:

    - active application
    - active window title
    - expected element existence
    - expected element disappearance
    - expected element current value
    """

    def verify(
        self,
        expected: ExpectedOutcome,
        scene: ScreenScene,
    ) -> VerificationResult:

        state = scene.observation.state

        if expected.require_scene_change:
            baseline = expected.baseline_scene_signature
            if baseline is None:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Scene-change verification has no baseline "
                        "semantic scene signature."
                    ),
                    confidence=1.0,
                )

            current = self._scene_signature(scene)
            if current == baseline:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Semantic screen scene did not change "
                        "after the GUI action."
                    ),
                    confidence=0.95,
                    metadata={
                        "scene_changed": False,
                    },
                )


        if (
            expected.expected_active_application
            is not None
        ):

            if (
                state.active_application
                != expected.expected_active_application
            ):

                return VerificationResult(
                    verified=False,
                    reason=(
                        "Active application does not "
                        "match expectation."
                    ),
                    confidence=1.0,
                    metadata={
                        "expected": (
                            expected.expected_active_application
                        ),
                        "actual": (
                            state.active_application
                        ),
                    },
                )


        if (
            expected.expected_window_title
            is not None
        ):

            if (
                state.active_window_title
                != expected.expected_window_title
            ):

                return VerificationResult(
                    verified=False,
                    reason=(
                        "Active window title does not "
                        "match expectation."
                    ),
                    confidence=1.0,
                    metadata={
                        "expected": (
                            expected.expected_window_title
                        ),
                        "actual": (
                            state.active_window_title
                        ),
                    },
                )


        if (
            expected.expected_element_label
            is not None
        ):

            found = scene.find_by_label(
                expected.expected_element_label
            )

            exists = bool(found)


            if (
                expected.element_should_exist
                and not exists
            ):

                return VerificationResult(
                    verified=False,
                    reason=(
                        "Expected element was not found."
                    ),
                    confidence=0.9,
                    metadata={
                        "expected_label": (
                            expected.expected_element_label
                        ),
                        "found": False,
                    },
                )


            if (
                not expected.element_should_exist
                and exists
            ):

                return VerificationResult(
                    verified=False,
                    reason=(
                        "Element was expected to disappear "
                        "but is still present."
                    ),
                    confidence=0.9,
                    metadata={
                        "expected_label": (
                            expected.expected_element_label
                        ),
                        "found": True,
                    },
                )


        if (
            expected.expected_element_current_value
            is not None
            and expected.expected_element_label
            is not None
        ):
            found = scene.find_by_label(
                expected.expected_element_label
            )

            if not found:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Expected value could not be checked "
                        "because the target element was not found."
                    ),
                    confidence=0.9,
                )

            actual_value = self._current_value(found[0])

            if actual_value != expected.expected_element_current_value:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Targeted semantic field does not contain "
                        "the expected value."
                    ),
                    confidence=0.95,
                    metadata={
                        "expected_label": (
                            expected.expected_element_label
                        ),
                        "expected_value": (
                            expected.expected_element_current_value
                        ),
                        "actual_value": actual_value,
                    },
                )


        if (
            expected.expected_element_kind
            is not None
        ):

            elements = scene.elements_of_kind(
                expected.expected_element_kind
            )

            exists = bool(elements)


            if (
                expected.element_should_exist
                and not exists
            ):

                return VerificationResult(
                    verified=False,
                    reason=(
                        "Expected element kind was not found."
                    ),
                    confidence=0.9,
                    metadata={
                        "expected_kind": (
                            expected.expected_element_kind
                        ),
                        "found": False,
                    },
                )


            if (
                not expected.element_should_exist
                and exists
            ):

                return VerificationResult(
                    verified=False,
                    reason=(
                        "Element kind was expected to "
                        "disappear but is still present."
                    ),
                    confidence=0.9,
                    metadata={
                        "expected_kind": (
                            expected.expected_element_kind
                        ),
                        "found": True,
                    },
                )


        return VerificationResult(
            verified=True,
            reason=(
                "Environment matches expected outcome."
            ),
            confidence=1.0,
        )


    @staticmethod
    def _current_value(element) -> str | None:
        metadata = element.metadata or {}

        value = metadata.get("current_value")
        if isinstance(value, str):
            return value.strip() or None

        return None


    @staticmethod
    def _scene_signature(
        scene: ScreenScene,
    ) -> tuple[tuple[object, ...], ...]:
        signature = []

        for element in scene.elements:
            metadata = element.metadata or {}
            signature.append(
                (
                    element.label,
                    element.kind,
                    int(element.x),
                    int(element.y),
                    int(element.width),
                    int(element.height),
                    metadata.get("automation_id"),
                    metadata.get("name"),
                    metadata.get("uia_enabled"),
                    metadata.get("uia_visible"),
                    metadata.get("uia_selected"),
                )
            )

        return tuple(
            sorted(
                signature,
                key=lambda item: repr(item),
            )
        )
