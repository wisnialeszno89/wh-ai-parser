from app.agent.agent_action import AgentAction


class AgentActionNormalizer:
    """
    Normalizes high-level semantic actions into supported agent actions.

    The model remains free to describe intent semantically. This layer
    translates only known, explicitly supported semantic actions into
    actions understood by the controlled execution layer.
    """

    _KNOWN_MAPPINGS = {
        "open_new_offer": "click_screen_element",
        "click": "click_screen_element",
        "click_ui_element": "click_screen_element",
    }

    _DEFAULT_TARGETS = {
        "open_new_offer": "Nowa oferta",
    }

    def normalize(
        self,
        action: AgentAction,
    ) -> AgentAction:
        canonical_name = self._KNOWN_MAPPINGS.get(
            action.name
        )

        if canonical_name is None:
            if action.name != "click_screen_element":
                return action

            canonical_name = action.name

        target = action.target

        if target is None:
            target = self._DEFAULT_TARGETS.get(
                action.name
            )

        return AgentAction(
            name=canonical_name,
            description=action.description,
            requires_confirmation=(
                action.requires_confirmation
            ),
            environment_requirement=(
                action.environment_requirement
            ),
            target=target,
            value=action.value,
            requires_environment_observation=True,
        )
