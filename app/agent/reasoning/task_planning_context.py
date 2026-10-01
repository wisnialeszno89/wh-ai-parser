from dataclasses import dataclass

from app.agent.perception.screen_scene import ScreenScene


@dataclass(frozen=True)
class TaskPlanningContext:
    """
    Model-facing context for initial task planning.

    This context is intentionally semantic. It contains no:
    - coordinates
    - window handles
    - runtime/provider identifiers
    - executor objects
    - raw perception internals
    """

    request_message: str

    intent: str

    capability_name: str | None = None

    capability_description: str | None = None

    skill_name: str | None = None

    skill_description: str | None = None

    scene: ScreenScene | None = None

    def to_payload(
        self,
    ) -> dict[str, object]:
        return {
            "request_message": self.request_message,
            "intent": self.intent,
            "capability": (
                {
                    "name": self.capability_name,
                    "description": (
                        self.capability_description
                    ),
                }
                if self.capability_name is not None
                else None
            ),
            "skill": (
                {
                    "name": self.skill_name,
                    "description": (
                        self.skill_description
                    ),
                }
                if self.skill_name is not None
                else None
            ),
            "scene": self._scene_payload(),
        }

    def _scene_payload(self) -> dict[str, object] | None:
        """
        Build a model-safe semantic summary of the latest scene.

        Only user-meaningful state is exposed. Provider/runtime metadata,
        coordinates, handles, automation ids and raw screenshots remain
        outside the model-facing payload.
        """

        if self.scene is None:
            return None

        state = self.scene.observation.state

        elements = []
        for element in self.scene.elements:
            item: dict[str, object] = {
                "kind": element.kind,
                "label": element.label,
                "interaction_capability": (
                    element.interaction_capability.value
                ),
            }

            if element.confidence is not None:
                item["confidence"] = element.confidence

            elements.append(item)

        return {
            "active_application": state.active_application,
            "active_window_title": state.active_window_title,
            "visible_elements": elements,
            "element_count": len(elements),
        }
