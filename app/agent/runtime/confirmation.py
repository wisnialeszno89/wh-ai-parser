from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from app.agent.agent_action import AgentAction


@dataclass(frozen=True)
class ConfirmationRequest:
    """One-time approval request for a specific semantic action."""

    token: str
    session_id: str
    action_name: str
    description: str
    target: str | None = None
    value: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "token": self.token,
            "session_id": self.session_id,
            "action": {
                "name": self.action_name,
                "description": self.description,
                "target": self.target,
                "value": self.value,
            },
        }


def action_confirmation_key(action: AgentAction) -> str:
    """Return a deterministic identity key for an exact semantic action."""

    payload = {
        "name": action.name,
        "description": action.description,
        "target": action.target,
        "value": action.value,
    }

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()
