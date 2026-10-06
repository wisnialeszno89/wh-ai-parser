from __future__ import annotations

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.learned_parameter import canonical_parameter_name
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
            if not isinstance(event.value, str):
                return None

            metadata = event.metadata or {}
            event_name = metadata.get("event_uia_name")
            event_control_type = metadata.get("event_uia_control_type")

            target = None
            parameter_name = None
            value_source = "literal"

            if (
                isinstance(event_name, str)
                and event_name.strip()
                and isinstance(event_control_type, str)
                and event_control_type.strip().casefold()
                in {"edit", "textbox", "input", "combobox"}
            ):
                target = event_name.strip()

                if metadata.get("semantic_text_input") is True:
                    parameter_name = canonical_parameter_name(
                        target
                    )
                    value_source = "parameter"

            if target is None:
                target = self._active_edit_target(scene)

            if target is None:
                return None

            return LearnedAction(
                name="write_text",
                target=target,
                value=event.value,
                description=f"Enter text into '{target}'.",
                value_source=value_source,
                parameter_name=parameter_name,
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

        metadata = event.metadata or {}
        event_name = metadata.get("event_uia_name")
        event_control_type = metadata.get("event_uia_control_type")

        # Prefer the semantic target captured at physical click time. The UI
        # can advance before the queued event is processed, so a later scene
        # must not erase an action that was unambiguously observed.
        if (
            isinstance(event_name, str)
            and event_name.strip()
            and isinstance(event_control_type, str)
            and event_control_type.strip().casefold()
            in {
                "button",
                "checkbox",
                "combobox",
                "hyperlink",
                "listitem",
                "menuitem",
                "radiobutton",
                "splitbutton",
                "tabitem",
                "treeitem",
            }
        ):
            return LearnedAction(
                name="click_screen_element",
                target=event_name.strip(),
                description=f"Activate '{event_name.strip()}'.",
            )

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
                element.x <= event.x < element.x + element.width
                and element.y <= event.y < element.y + element.height
            ):
                candidates.append(element)

        target_element = HumanActionInterpreter._resolve_click_candidate(
            candidates
        )
        if target_element is None:
            return None

        target = target_element.label
        if not target or not target.strip():
            return None

        return LearnedAction(
            name="click_screen_element",
            target=target.strip(),
            description=f"Activate '{target.strip()}'.",
        )

    @staticmethod
    def _resolve_click_candidate(candidates):
        if len(candidates) == 1:
            return candidates[0]

        # Accessibility trees often contain a clickable parent/container
        # around the actual clickable child. Prefer the unique smallest
        # candidate only when its bounds are strictly contained by every
        # other candidate. Partial overlaps and equal/identical bounds remain
        # ambiguous and therefore fail closed.
        for candidate in candidates:
            assert candidate.x is not None
            assert candidate.y is not None
            assert candidate.width is not None
            assert candidate.height is not None

            c_left = candidate.x
            c_top = candidate.y
            c_right = candidate.x + candidate.width
            c_bottom = candidate.y + candidate.height

            strictly_inside_all = True

            for other in candidates:
                if other is candidate:
                    continue

                assert other.x is not None
                assert other.y is not None
                assert other.width is not None
                assert other.height is not None

                o_left = other.x
                o_top = other.y
                o_right = other.x + other.width
                o_bottom = other.y + other.height

                if not (
                    o_left <= c_left
                    and o_top <= c_top
                    and c_right <= o_right
                    and c_bottom <= o_bottom
                    and (
                        c_left > o_left
                        or c_top > o_top
                        or c_right < o_right
                        or c_bottom < o_bottom
                    )
                ):
                    strictly_inside_all = False
                    break

            if strictly_inside_all:
                return candidate

        return None

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
