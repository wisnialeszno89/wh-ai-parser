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
    """

    def verify(
        self,
        expected: ExpectedOutcome,
        scene: ScreenScene,
    ) -> VerificationResult:

        state = scene.observation.state


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
