from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class AgentExperience:
    """
    Durable, model-safe memory of an agent outcome.

    Raw user requests and machine-specific runtime identifiers are intentionally
    not part of this record.
    """

    experience_id: str
    kind: str
    application: str | None
    intent: str | None
    workflow_id: str | None
    outcome: str
    summary: str
    created_at: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            "experience_id": self.experience_id,
            "kind": self.kind,
            "application": self.application,
            "intent": self.intent,
            "workflow_id": self.workflow_id,
            "outcome": self.outcome,
            "summary": self.summary,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> "AgentExperience":
        return cls(
            experience_id=str(payload.get("experience_id") or ""),
            kind=str(payload.get("kind") or ""),
            application=(
                str(payload["application"])
                if payload.get("application") is not None
                else None
            ),
            intent=(
                str(payload["intent"])
                if payload.get("intent") is not None
                else None
            ),
            workflow_id=(
                str(payload["workflow_id"])
                if payload.get("workflow_id") is not None
                else None
            ),
            outcome=str(payload.get("outcome") or ""),
            summary=str(payload.get("summary") or ""),
            created_at=(
                str(payload["created_at"])
                if payload.get("created_at") is not None
                else None
            ),
            metadata=dict(payload.get("metadata") or {}),
        )


class AgentMemoryRepository:
    """
    Atomic JSON repository for durable agent experiences.
    """

    def __init__(self, directory: str | Path | None = None) -> None:
        root = (
            directory
            if directory is not None
            else os.environ.get(
                "AGENT_MEMORY_STORE_DIR",
                "runtime_data/agent_memory",
            )
        )
        self.directory = Path(root)

    def save(self, experience: AgentExperience) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

        filename = self._filename(experience.experience_id)
        destination = self.directory / filename
        temporary = destination.with_suffix(destination.suffix + ".tmp")

        temporary.write_text(
            json.dumps(
                experience.to_payload(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        temporary.replace(destination)

    def get(self, experience_id: str) -> AgentExperience | None:
        path = self.directory / self._filename(experience_id)
        if not path.exists():
            return None

        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
        if not isinstance(payload, dict):
            raise ValueError("Agent experience JSON must contain an object.")

        return AgentExperience.from_payload(payload)

    def all(self) -> tuple[AgentExperience, ...]:
        if not self.directory.exists():
            return ()

        experiences = []
        for path in sorted(self.directory.glob("*.json")):
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )
            if isinstance(payload, dict):
                experiences.append(
                    AgentExperience.from_payload(payload)
                )

        return tuple(experiences)

    @staticmethod
    def _filename(experience_id: str) -> str:
        digest = hashlib.sha256(
            experience_id.encode("utf-8")
        ).hexdigest()
        return f"{digest}.json"
