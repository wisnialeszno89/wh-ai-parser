from app.agent.agent_action import AgentAction

from app.agent.runtime.execution_context import ExecutionContext

from app.agent.verification.expected_outcome import ExpectedOutcome


class ExpectationResolver:
    """
    Resolves an expected observable outcome for an action.

    The resolver intentionally returns None when an action
    does not require environment verification.
    """

    def resolve(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome | None:
        expectation = self._resolve_from_context(action, context)
        if expectation is not None:
            return expectation

        browser_expectation = self._resolve_browser_default(action)
        if browser_expectation is not None:
            return browser_expectation

        return self._resolve_default(action, context)

    def _resolve_from_context(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome | None:
        expectations = context.get_value("expected_outcomes")

        if not isinstance(expectations, dict):
            return None

        expectation = expectations.get(action.name)
        if isinstance(expectation, ExpectedOutcome):
            return expectation

        return None

    @staticmethod
    def _resolve_browser_default(
        action: AgentAction,
    ) -> ExpectedOutcome | None:
        """
        Resolve deterministic verification for browser actions.

        Navigation is verified against the resulting URL. Text entry and
        select operations are verified against the resulting semantic field
        value.

        Click and back deliberately have no generic default post-state.
        A caller may supply an explicit ExpectedOutcome when one is required.
        """
        if action.name == "browser_navigate":
            if not isinstance(action.value, str) or not action.value.strip():
                return None

            return ExpectedOutcome(
                description=(
                    "The browser should be at the requested URL "
                    "after navigation."
                ),
                expected_browser_url=action.value.strip(),
            )

        if action.name in {"browser_write_text", "browser_select_option"}:
            target = (
                action.target.strip()
                if isinstance(action.target, str)
                else None
            )
            value = (
                action.value
                if isinstance(action.value, str)
                else None
            )
            if not target or not value:
                return None

            return ExpectedOutcome(
                description=(
                    "The targeted browser field should expose "
                    "the requested value after execution."
                ),
                expected_browser_element_label=target,
                expected_browser_element_current_value=value,
            )

        return None

    def _resolve_default(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome | None:
        if context.current_scene is None:
            return None

        if action.name == "click_screen_element":
            return ExpectedOutcome(
                description=(
                    "The semantic screen scene should change "
                    "after the GUI click."
                ),
                require_scene_change=True,
                baseline_scene_signature=self._scene_signature(
                    context.current_scene
                ),
            )

        if action.name == "write_text":
            target = (
                action.target.strip()
                if isinstance(action.target, str)
                else None
            )
            value = action.value if isinstance(action.value, str) else None

            if not target or not value:
                return None

            return ExpectedOutcome(
                description=(
                    "The targeted semantic field should contain "
                    "the requested text after execution."
                ),
                expected_element_label=target,
                element_should_exist=True,
                expected_element_current_value=value,
            )

        return None

    @staticmethod
    def _scene_signature(
        scene,
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
