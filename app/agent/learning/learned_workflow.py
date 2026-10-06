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
