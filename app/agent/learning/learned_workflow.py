from __future__ import annotations

from dataclasses import dataclass, field

from app.agent.learning.semantic_snapshot import SemanticSnapshot


@dataclass(frozen=True)
class LearnedAction:
    """
    Semantic user action captured during a teaching session.

    No physical coordinates or platform-specific identifiers are stored.
    """

    name: str
    target: str | None = None
    value: str | None = None
    description: str = ""

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, object],
    ) -> "LearnedAction":
        return cls(
            name=str(payload.get("name") or ""),
            target=(
                str(payload["target"])
                if payload.get("target") is not None
                else None
            ),
            value=(
                str(payload["value"])
                if payload.get("value") is not None
                else None
            ),
            description=str(
                payload.get("description") or ""
            ),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "target": self.target,
            "value": self.value,
            "description": self.description,
        }


@dataclass(frozen=True)
class LearnedWorkflowStep:
    """
    One transition demonstrated by a user.

    The before/after snapshots make the learned procedure explainable
    instead of reducing it to a fragile macro.
    """

    index: int
    action: LearnedAction
    before: SemanticSnapshot
    after: SemanticSnapshot | None = None
    notes: str = ""

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, object],
    ) -> "LearnedWorkflowStep":
        before_payload = payload.get("before")
        after_payload = payload.get("after")
        action_payload = payload.get("action")

        if not isinstance(action_payload, dict):
            raise ValueError("Workflow step action is invalid.")
        if not isinstance(before_payload, dict):
            raise ValueError("Workflow step before snapshot is invalid.")
        if after_payload is not None and not isinstance(after_payload, dict):
            raise ValueError("Workflow step after snapshot is invalid.")

        from app.agent.learning.semantic_snapshot import SemanticSnapshot

        return cls(
            index=int(payload.get("index") or 0),
            action=LearnedAction.from_payload(action_payload),
            before=SemanticSnapshot.from_payload(before_payload),
            after=(
                SemanticSnapshot.from_payload(after_payload)
                if after_payload is not None
                else None
            ),
            notes=str(payload.get("notes") or ""),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "index": self.index,
            "action": self.action.to_payload(),
            "before": self.before.to_payload(),
            "after": (
                self.after.to_payload()
                if self.after is not None
                else None
            ),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class LearnedWorkflow:
    """
    Portable workflow learned from a human demonstration.

    A workflow describes intent and semantic transitions. It does not
    hard-code screen coordinates or a particular computer's window handles.
    """

    workflow_id: str
    name: str
    application: str | None
    trigger: str
    steps: tuple[LearnedWorkflowStep, ...] = ()
    version: int = 1
    notes: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, object],
    ) -> "LearnedWorkflow":
        steps_payload = payload.get("steps") or []
        if not isinstance(steps_payload, list):
            raise ValueError("Workflow steps must be a list.")

        steps = tuple(
            LearnedWorkflowStep.from_payload(step)
            for step in steps_payload
            if isinstance(step, dict)
        )

        return cls(
            workflow_id=str(
                payload.get("workflow_id") or ""
            ),
            name=str(
                payload.get("name") or ""
            ),
            application=(
                str(payload["application"])
                if payload.get("application") is not None
                else None
            ),
            trigger=str(
                payload.get("trigger") or ""
            ),
            steps=steps,
            version=int(
                payload.get("version") or 1
            ),
            notes=str(
                payload.get("notes") or ""
            ),
            metadata=dict(
                payload.get("metadata") or {}
            ),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "application": self.application,
            "trigger": self.trigger,
            "version": self.version,
            "notes": self.notes,
            "steps": [
                step.to_payload()
                for step in self.steps
            ],
            "metadata": dict(self.metadata),
        }
