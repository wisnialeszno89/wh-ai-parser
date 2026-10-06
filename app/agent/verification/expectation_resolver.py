from app.agent.agent_action import AgentAction

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)


class ExpectationResolver:
    """
    Resolves an expected observable outcome for an action.

    The resolver intentionally returns None when an action
    does not require environment verification.

    This keeps semantic and abstract actions independent from
    GUI-specific expectations.

    Environment-specific implementations may later extend or
    replace these expectations.
    """

    def resolve(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome | None:

        expectation = self._resolve_from_context(
            action,
            context,
        )

        if expectation is not None:
            return expectation

        return self._resolve_default(
            action,
            context,
        )

    def _resolve_from_context(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome | None:
        """
        Resolve an explicitly registered expectation from
        the execution context.

        The context allows environment-specific executors or
        future planners to provide precise expectations without
        coupling this resolver to a specific application.
        """

        expectations = context.get_value(
            "expected_outcomes"
        )

        if not isinstance(
            expectations,
            dict,
        ):
            return None

        expectation = expectations.get(
            action.name
        )

        if isinstance(
            expectation,
            ExpectedOutcome,
        ):
            return expectation

        return None

    def _resolve_default(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExpectedOutcome | None:
        """
        Resolve built-in expectations for generic actions.

        GUI clicks receive a conservative default expectation:
        the semantic screen scene must change after the click.
        Text entry receives a stronger semantic verification:
        the targeted field should expose the requested value after
        execution.

        Abstract and other actions remain unverified by default.
        """

        if context.current_scene is None:
            return None

        if action.name == "click_screen_element":
            return ExpectedOutcome(
                description=(
                    "The semantic screen scene should change "
                    "after the GUI click."
                ),
                require_scene_change=True,
                baseline_scene_signature=(
                    self._scene_signature(context.current_scene)
                ),
            )

        if action.name == "write_text":
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

        return tuple(
            sorted(
                signature,
                key=lambda item: repr(item),
            )
        )
