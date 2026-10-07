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


def browser_confirmation_context_key(
    page,
    action: AgentAction,
) -> str:
    """Return a stable local fingerprint for the approved browser state."""

    from app.agent.adapters.browser_adapter import BrowserPage

    if not isinstance(page, BrowserPage):
        raise TypeError("Browser confirmation requires BrowserPage context.")

    target = action.target.strip().casefold() if isinstance(action.target, str) else ""
    candidates = [
        element
        for element in page.elements
        if isinstance(element.label, str)
        and element.label.strip().casefold() == target
    ]

    payload = {
        "url": page.url,
        "title": page.title,
        "target": target,
        "target_count": len(candidates),
        "target_elements": [
            {
                "kind": element.kind,
                "interaction_capability": element.interaction_capability,
                "current_value": element.current_value,
                "confidence": element.confidence,
            }
            for element in candidates
        ],
    }

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


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
