from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from app.agent.adapters.browser_adapter import BrowserPage
from app.agent.perception.screen_scene import ScreenScene
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.verification_result import VerificationResult


class OutcomeVerifier:
    """
    Verifies expected post-action state against a semantic desktop scene
    or a provider-neutral BrowserPage snapshot.
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
                    metadata={"scene_changed": False},
                )

        if expected.expected_active_application is not None:
            if (
                state.active_application
                != expected.expected_active_application
            ):
                return VerificationResult(
                    verified=False,
                    reason="Active application does not match expectation.",
                    confidence=1.0,
                    metadata={
                        "expected": expected.expected_active_application,
                        "actual": state.active_application,
                    },
                )

        if expected.expected_window_title is not None:
            if state.active_window_title != expected.expected_window_title:
                return VerificationResult(
                    verified=False,
                    reason="Active window title does not match expectation.",
                    confidence=1.0,
                    metadata={
                        "expected": expected.expected_window_title,
                        "actual": state.active_window_title,
                    },
                )

        if expected.expected_semantic_elements:
            semantic_result = self._verify_semantic_elements(
                expected.expected_semantic_elements,
                scene,
            )
            if semantic_result is not None:
                return semantic_result

        if expected.expected_element_label is not None:
            found = scene.find_by_label(expected.expected_element_label)
            exists = bool(found)

            if expected.element_should_exist and not exists:
                return VerificationResult(
                    verified=False,
                    reason="Expected element was not found.",
                    confidence=0.9,
                    metadata={
                        "expected_label": expected.expected_element_label,
                        "found": False,
                    },
                )

            if not expected.element_should_exist and exists:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Element was expected to disappear "
                        "but is still present."
                    ),
                    confidence=0.9,
                    metadata={
                        "expected_label": expected.expected_element_label,
                        "found": True,
                    },
                )

        if (
            expected.expected_element_current_value is not None
            and expected.expected_element_label is not None
        ):
            found = scene.find_by_label(expected.expected_element_label)

            if not found:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Expected value could not be checked because "
                        "the target element was not found."
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
                        "expected_label": expected.expected_element_label,
                        "expected_value": (
                            expected.expected_element_current_value
                        ),
                        "actual_value": actual_value,
                    },
                )

        if expected.expected_element_kind is not None:
            elements = scene.elements_of_kind(expected.expected_element_kind)
            exists = bool(elements)

            if expected.element_should_exist and not exists:
                return VerificationResult(
                    verified=False,
                    reason="Expected element kind was not found.",
                    confidence=0.9,
                    metadata={
                        "expected_kind": expected.expected_element_kind,
                        "found": False,
                    },
                )

            if not expected.element_should_exist and exists:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Element kind was expected to disappear "
                        "but is still present."
                    ),
                    confidence=0.9,
                    metadata={
                        "expected_kind": expected.expected_element_kind,
                        "found": True,
                    },
                )

        return VerificationResult(
            verified=True,
            reason="Environment matches expected outcome.",
            confidence=1.0,
        )

    def verify_browser(
        self,
        expected: ExpectedOutcome,
        page: BrowserPage | None,
    ) -> VerificationResult:
        """
        Verify a browser action against the fresh semantic BrowserPage
        returned by BrowserAdapter after execution.
        """
        if not isinstance(page, BrowserPage):
            return VerificationResult(
                verified=False,
                reason="Browser verification has no fresh BrowserPage.",
                confidence=1.0,
            )

        if expected.require_browser_change:
            baseline = expected.baseline_browser_signature
            if baseline is None:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Browser change verification has no baseline "
                        "semantic page signature."
                    ),
                    confidence=1.0,
                )

            current = self._browser_page_signature(page)
            if current == baseline:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Browser semantic page did not change "
                        "after the browser action."
                    ),
                    confidence=0.95,
                    metadata={"browser_page_changed": False},
                )

        if expected.expected_browser_url is not None:
            actual_url = self._normalize_url(page.url)
            expected_url = self._normalize_url(expected.expected_browser_url)

            if actual_url != expected_url:
                return VerificationResult(
                    verified=False,
                    reason="Browser URL does not match expectation.",
                    confidence=0.95,
                    metadata={
                        "expected_url": expected.expected_browser_url,
                        "actual_url": page.url,
                    },
                )

        if expected.expected_browser_title is not None:
            if page.title != expected.expected_browser_title:
                return VerificationResult(
                    verified=False,
                    reason="Browser page title does not match expectation.",
                    confidence=0.95,
                    metadata={
                        "expected_title": expected.expected_browser_title,
                        "actual_title": page.title,
                    },
                )

        if (
            expected.expected_browser_element_label is not None
            or expected.expected_browser_element_current_value is not None
        ):
            label = expected.expected_browser_element_label

            candidates = [
                element
                for element in page.elements
                if (
                    label is None
                    or element.label.strip().casefold()
                    == label.strip().casefold()
                )
            ]

            if not candidates:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Expected browser semantic element was not found."
                    ),
                    confidence=0.95,
                    metadata={
                        "expected_label": label,
                        "found": False,
                    },
                )

            if len(candidates) > 1:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Expected browser semantic element is ambiguous."
                    ),
                    confidence=0.95,
                    metadata={
                        "expected_label": label,
                        "candidate_count": len(candidates),
                    },
                )

            element = candidates[0]

            if (
                expected.expected_browser_element_current_value
                is not None
            ):
                actual_value = element.current_value

                if actual_value != (
                    expected.expected_browser_element_current_value
                ):
                    return VerificationResult(
                        verified=False,
                        reason=(
                            "Browser semantic field does not contain "
                            "the expected value."
                        ),
                        confidence=0.95,
                        metadata={
                            "expected_label": label,
                            "expected_value": (
                                expected.expected_browser_element_current_value
                            ),
                            "actual_value": actual_value,
                        },
                    )

        return VerificationResult(
            verified=True,
            reason="Browser page matches expected outcome.",
            confidence=1.0,
        )

    @staticmethod
    def _browser_page_signature(page: BrowserPage) -> tuple[object, ...]:
        elements = []
        for element in page.elements:
            elements.append(
                (
                    element.label,
                    element.kind,
                    element.interaction_capability,
                    element.current_value,
                )
            )

        return (
            page.url,
            page.title,
            page.text,
            tuple(elements),
        )

    @staticmethod
    def _normalize_url(value: str) -> str:
        parsed = urlsplit(value.strip())
        return urlunsplit(
            (
                parsed.scheme.casefold(),
                parsed.netloc.casefold(),
                parsed.path or "/",
                parsed.query,
                parsed.fragment,
            )
        )

    @staticmethod
    def _verify_semantic_elements(
        requirements,
        scene: ScreenScene,
    ) -> VerificationResult | None:
        for requirement in requirements:
            if not isinstance(requirement, dict):
                continue

            kind = requirement.get("kind")
            label = requirement.get("label")

            candidates = [
                element
                for element in scene.elements
                if (
                    (
                        not isinstance(kind, str)
                        or element.kind.casefold() == kind.casefold()
                    )
                    and (
                        not isinstance(label, str)
                        or (
                            isinstance(element.label, str)
                            and element.label.casefold() == label.casefold()
                        )
                    )
                )
            ]

            if not candidates:
                return VerificationResult(
                    verified=False,
                    reason="Expected semantic element was not found.",
                    confidence=0.95,
                    metadata={"requirement": dict(requirement)},
                )

            state_keys = (
                "current_value",
                "uia_selected",
                "document_scope",
            )

            matched = False
            for element in candidates:
                metadata = element.metadata or {}
                state_matches = True

                for key in state_keys:
                    if key not in requirement:
                        continue

                    if metadata.get(key) != requirement.get(key):
                        state_matches = False
                        break

                if state_matches:
                    matched = True
                    break

            if not matched:
                return VerificationResult(
                    verified=False,
                    reason=(
                        "Expected semantic element state was not observed."
                    ),
                    confidence=0.95,
                    metadata={
                        "requirement": dict(requirement),
                        "candidates": [
                            {
                                "label": element.label,
                                "kind": element.kind,
                                "current_value": (
                                    element.metadata or {}
                                ).get("current_value"),
                                "uia_selected": (
                                    element.metadata or {}
                                ).get("uia_selected"),
                                "document_scope": (
                                    element.metadata or {}
                                ).get("document_scope"),
                            }
                            for element in candidates
                        ],
                    },
                )

        return None

    @staticmethod
    def _current_value(element) -> str | None:
        value = (element.metadata or {}).get("current_value")
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

        return tuple(sorted(signature, key=lambda item: repr(item)))
