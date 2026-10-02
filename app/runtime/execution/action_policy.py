from __future__ import annotations

from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)


class ActionPolicy:
    """
    Defines which interaction actions are currently enabled
    for the universal robot.

    This policy does not inspect vision state and does not touch hardware.
    """

    def __init__(
        self,
        *,
        allowed_actions: frozenset[InteractionAction] | None = None,
    ) -> None:
        self._allowed_actions = (
            allowed_actions
            if allowed_actions is not None
            else frozenset({
                InteractionAction.CLICK,
                InteractionAction.WRITE,
            })
        )

    def can_execute(self, action: InteractionAction) -> bool:
        return action in self._allowed_actions
