"""Structured, operator-approved experience records for NaviMind.

Experience records intentionally store semantic workflow steps only. They must
not contain screenshots, native window handles, customer records, passwords,
raw offer requests, or document contents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


_ALLOWED_ACTIONS = frozenset(
    {
        "observe",
        "activate_window",
        "click",
        "type",
        "select",
        "scroll",
        "drag",
        "navigate",
        "verify",
        "manual",
    }
)
_TOKEN_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,79}$")


def _validate_token(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"experience_{field_name}_invalid")
    normalized = value.strip().casefold()
    if not _TOKEN_PATTERN.fullmatch(normalized):
        raise ValueError(f"experience_{field_name}_invalid")
    return normalized


def _validate_text(value: str, field_name: str, *, limit: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"experience_{field_name}_invalid")
    normalized = value.strip()
    if not normalized or len(normalized) > limit:
        raise ValueError(f"experience_{field_name}_invalid")
    return normalized


@dataclass(frozen=True)
class ExperienceStep:
    """One semantic, repeatable step from a demonstrated workflow."""

    action: str
    target: str
    purpose: str
    verification: str

    def __post_init__(self) -> None:
        action = _validate_token(self.action, "action")
        if action not in _ALLOWED_ACTIONS:
            raise ValueError("experience_action_not_allowed")
        object.__setattr__(self, "action", action)
        object.__setattr__(
            self,
            "target",
            _validate_token(self.target, "step_target"),
        )
        object.__setattr__(
            self,
            "purpose",
            _validate_text(self.purpose, "step_purpose", limit=180),
        )
        object.__setattr__(
            self,
            "verification",
            _validate_text(self.verification, "step_verification", limit=180),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "action": self.action,
            "target": self.target,
            "purpose": self.purpose,
            "verification": self.verification,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ExperienceStep":
        if not isinstance(data, dict):
            raise TypeError("experience_step_payload_invalid")
        return cls(
            action=data.get("action"),  # type: ignore[arg-type]
            target=data.get("target"),  # type: ignore[arg-type]
            purpose=data.get("purpose"),  # type: ignore[arg-type]
            verification=data.get("verification"),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class ExperienceEpisode:
    """A completed demonstration isolated to one company and operator."""

    tenant_id: str
    operator_id: str
    application_id: str
    task_kind: str
    tags: tuple[str, ...]
    steps: tuple[ExperienceStep, ...]
    outcome: str
    approved_by_operator: bool = False
    episode_id: str = field(default_factory=lambda: uuid4().hex)
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        for field_name in ("tenant_id", "operator_id", "application_id", "task_kind"):
            object.__setattr__(
                self,
                field_name,
                _validate_token(getattr(self, field_name), field_name),
            )
        tags = tuple(_validate_token(tag, "tag") for tag in self.tags)
        if len(tags) > 20 or len(set(tags)) != len(tags):
            raise ValueError("experience_tags_invalid")
        object.__setattr__(self, "tags", tags)
        if not isinstance(self.steps, tuple) or not 1 <= len(self.steps) <= 60:
            raise ValueError("experience_steps_invalid")
        if any(not isinstance(step, ExperienceStep) for step in self.steps):
            raise TypeError("experience_steps_invalid")
        if self.outcome not in {"completed", "manual_review", "failed"}:
            raise ValueError("experience_outcome_invalid")
        if not isinstance(self.approved_by_operator, bool):
            raise TypeError("experience_approval_invalid")
        object.__setattr__(
            self,
            "episode_id",
            _validate_token(self.episode_id, "episode_id"),
        )
        object.__setattr__(
            self,
            "created_at_utc",
            _validate_text(self.created_at_utc, "created_at", limit=64),
        )

    def to_storage_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "episode_id": self.episode_id,
            "tenant_id": self.tenant_id,
            "operator_id": self.operator_id,
            "application_id": self.application_id,
            "task_kind": self.task_kind,
            "tags": list(self.tags),
            "steps": [step.to_dict() for step in self.steps],
            "outcome": self.outcome,
            "approved_by_operator": self.approved_by_operator,
            "created_at_utc": self.created_at_utc,
        }

    def to_prompt_payload(self) -> dict[str, object]:
        """Project only the approved workflow, never company/operator identity."""
        if not self.approved_by_operator:
            raise ValueError("experience_episode_not_approved")
        return {
            "application": self.application_id,
            "task_kind": self.task_kind,
            "tags": list(self.tags),
            "steps": [step.to_dict() for step in self.steps],
            "outcome": self.outcome,
        }

    @classmethod
    def from_storage_dict(cls, data: dict[str, object]) -> "ExperienceEpisode":
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ValueError("experience_record_schema_unsupported")
        raw_tags = data.get("tags")
        raw_steps = data.get("steps")
        if not isinstance(raw_tags, list) or not isinstance(raw_steps, list):
            raise ValueError("experience_record_payload_invalid")
        return cls(
            tenant_id=data.get("tenant_id"),  # type: ignore[arg-type]
            operator_id=data.get("operator_id"),  # type: ignore[arg-type]
            application_id=data.get("application_id"),  # type: ignore[arg-type]
            task_kind=data.get("task_kind"),  # type: ignore[arg-type]
            tags=tuple(raw_tags),  # type: ignore[arg-type]
            steps=tuple(ExperienceStep.from_dict(item) for item in raw_steps),
            outcome=data.get("outcome"),  # type: ignore[arg-type]
            approved_by_operator=data.get("approved_by_operator", False),  # type: ignore[arg-type]
            episode_id=data.get("episode_id", uuid4().hex),  # type: ignore[arg-type]
            created_at_utc=data.get("created_at_utc"),  # type: ignore[arg-type]
        )
