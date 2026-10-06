from __future__ import annotations

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.learned_workflow import LearnedAction
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.screen_scene import ScreenScene


class HumanActionInterpreter:
    """
    Converts transient local input events into semantic learned actions.

    The event coordinates are used only during interpretation. They are never
    included in LearnedAction or persisted workflow data.
    """

    def interpret(
        self,
        *,
        event: HumanActionEvent,
        scene: ScreenScene,
    ) -> LearnedAction | None:
        action_type = event.action_type.strip().casefold()

        if action_type in {"click", "left_click", "mouse_click"}:
            return self._interpret_click(event=event, scene=scene)

        if action_type in {"write_text", "type_text"}:
            if not isinstance(event.value, str) or not event.value:
                return None

            target = self._active_edit_target(scene)
            if target is None:
                return None

            return LearnedAction(
                name="write_text",
                target=target,
                value=event.value,
                description=f"Enter text into '{target}'.",
            )

        return None

    @staticmethod
    def _interpret_click(
        *,
        event: HumanActionEvent,
        scene: ScreenScene,
    ) -> LearnedAction | None:
        if event.x is None or event.y is None:
            return None

        candidates = []

        for element in scene.elements:
            if (
                element.interaction_capability
                is not InteractionCapability.CLICKABLE
            ):
                continue

            if not element.has_bounds or element.label is None:
                continue

            assert element.x is not None
            assert element.y is not None
            assert element.width is not None
            assert element.height is not None

            if (
                element.x <= event.x <= element.x + element.width
                and element.y <= event.y <= element.y + element.height
            ):
                candidates.append(element)

        if len(candidates) != 1:
            return None

        target = candidates[0].label
        if not target or not target.strip():
            return None

        return LearnedAction(
            name="click_screen_element",
            target=target.strip(),
            description=f"Activate '{target.strip()}'.",
        )

    @staticmethod
    def _active_edit_target(
        scene: ScreenScene,
    ) -> str | None:
        candidates = []

        for element in scene.elements:
            if element.label is None:
                continue

            kind = element.kind.casefold()
            if kind not in {
                "edit",
                "textbox",
                "input",
                "combobox",
            }:
                continue

            candidates.append(element.label)

        if len(candidates) == 1:
            return candidates[0].strip() or None

        return None
