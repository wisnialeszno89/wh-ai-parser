from dataclasses import dataclass, field
from typing import Any

from app.agent.bridge.world_state import WorldState


@dataclass(frozen=True)
class AgentTaskContract:
    """
    Versioned JSON boundary between NaviMind and the desktop agent.

    NaviMind decides what the task means and may enrich the context.
    wh-ai-parser owns observation, semantic action validation, execution
    and verification.
    """

    task_id: str
    goal: str
    intent: str
    session_id: str | None = None
    user_id: str | None = None
    capability: dict[str, object] | None = None
    skill: dict[str, object] | None = None
    world: WorldState = field(default_factory=WorldState)
    offer_workflow: dict[str, object] | None = None
    knowledge: dict[str, object] | None = None
    experience: tuple[dict[str, object], ...] = ()
    constraints: dict[str, object] = field(
        default_factory=lambda: {
            "semantic_only": True,
            "max_actions": 1,
            "verify_each_action": True,
        }
    )
    metadata: dict[str, object] = field(default_factory=dict)
    version: str = "1"

    def to_payload(self) -> dict[str, object]:
        return {
            "version": self.version,
            "task_id": self.task_id,
            "goal": self.goal,
            "intent": self.intent,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "capability": self.capability,
            "skill": self.skill,
            "world": self.world.to_payload(),
            "offer_workflow": self.offer_workflow,
            "knowledge": self.knowledge,
            "experience": list(self.experience),
            "constraints": self.constraints,
            "metadata": self.metadata,
        }
