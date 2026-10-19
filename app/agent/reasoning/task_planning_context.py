from dataclasses import dataclass

from app.agent.adapters.browser_adapter import BrowserPage
from app.agent.perception.screen_scene import ScreenScene
from app.agent.reasoning.knowledge_context import KnowledgeContext
from app.agent.world.semantic_world_model import SemanticWorldModel


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
    - provider-local browser locators
    """

    request_message: str
    intent: str
    session_id: str | None = None
    user_id: str | None = None
    operating_mode: str = "execute"
    capability_name: str | None = None
    capability_description: str | None = None
    skill_name: str | None = None
    skill_description: str | None = None
    scene: ScreenScene | None = None
    browser_page: BrowserPage | None = None
    offer_workflow: dict[str, object] | None = None
    application_knowledge: dict[str, object] | None = None
    external_knowledge: KnowledgeContext | None = None
    experience: tuple[dict[str, object], ...] = ()
    learned_workflows: tuple[dict[str, object], ...] = ()
    adapters: tuple[dict[str, object], ...] = ()
    world: SemanticWorldModel | None = None

    def to_payload(
        self,
    ) -> dict[str, object]:
        return {
            "request_message": self.request_message,
            "intent": self.intent,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "operating_mode": self.operating_mode,
            "capability": (
                {
                    "name": self.capability_name,
                    "description": self.capability_description,
                }
                if self.capability_name is not None
                else None
            ),
            "skill": (
                {
                    "name": self.skill_name,
                    "description": self.skill_description,
                }
                if self.skill_name is not None
                else None
            ),
            "scene": self._scene_payload(),
            "offer_workflow": self.offer_workflow,
            "application_knowledge": self.application_knowledge,
            "external_knowledge": (
                self.external_knowledge.to_payload()
                if self.external_knowledge is not None
                else None
            ),
            "experience": list(self.experience),
            "learned_workflows": list(self.learned_workflows),
            "adapters": list(self.adapters),
            "world": (
                self.world.to_payload()
                if self.world is not None
                else None
            ),
        }

    def _scene_payload(self) -> dict[str, object] | None:
        if self.scene is None:
            return None

        state = self.scene.observation.state
        elements = []

        for element in self.scene.elements[:80]:
            item: dict[str, object] = {
                "kind": element.kind,
                "label": element.label,
                "interaction_capability": (
                    element.interaction_capability.value
                ),
            }

            if element.confidence is not None:
                item["confidence"] = element.confidence

            metadata = element.metadata or {}
            current_value = metadata.get("current_value")
            selected = metadata.get("uia_selected")

            if isinstance(current_value, str):
                item["current_value"] = current_value

            if isinstance(selected, bool):
                item["selected"] = selected

            elements.append(item)

        return {
            "active_application": state.active_application,
            "active_window_title": state.active_window_title,
            "visible_elements": elements,
            "element_count": len(self.scene.elements),
            "included_element_count": len(elements),
        }
