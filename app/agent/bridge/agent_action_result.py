from dataclasses import dataclass
from typing import Any

from app.agent.bridge.world_state import WorldState


@dataclass(frozen=True)
class AgentActionResult:
    """Stable semantic execution result that can be returned to NaviMind."""

    action_id: str
    name: str
    target: str | None
    value: str | None
    success: bool
    verified: bool
    reason: str | None = None
    world_state: WorldState | None = None
    metadata: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "name": self.name,
            "target": self.target,
            "value": self.value,
            "success": self.success,
            "verified": self.verified,
            "reason": self.reason,
            "world_state": (
                self.world_state.to_payload()
                if self.world_state is not None
                else None
            ),
            "metadata": self.metadata or {},
        }
