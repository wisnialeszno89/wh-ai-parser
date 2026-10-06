from __future__ import annotations

from dataclasses import dataclass

from app.agent.learning.learned_workflow import (
    LearnedAction,
    LearnedWorkflow,
    LearnedWorkflowStep,
)
from app.agent.learning.semantic_snapshot import SemanticSnapshot


@dataclass
class _Recording:
    workflow_id: str
    name: str
    application: str | None
    trigger: str
    steps: list[LearnedWorkflowStep]


class LearningRecorder:
    """
    Collects one human demonstration into a semantic workflow.

    The recorder is intentionally independent from GUI technologies.
    A platform adapter is responsible for translating observed user
    interactions into LearnedAction objects.
    """

    def __init__(self) -> None:
        self._recording: _Recording | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording is not None

    def start(
        self,
        *,
        workflow_id: str,
        name: str,
        trigger: str,
        application: str | None = None,
    ) -> None:
        if self._recording is not None:
            raise RuntimeError("A learning session is already recording.")

        self._recording = _Recording(
            workflow_id=workflow_id,
            name=name,
            application=application,
            trigger=trigger,
            steps=[],
        )

    def record_step(
        self,
        *,
        action: LearnedAction,
        before: SemanticSnapshot,
        after: SemanticSnapshot | None = None,
        notes: str = "",
    ) -> LearnedWorkflowStep:
        recording = self._recording
        if recording is None:
            raise RuntimeError("No learning session is active.")

        step = LearnedWorkflowStep(
            index=len(recording.steps) + 1,
            action=action,
            before=before,
            after=after,
            notes=notes,
        )
        recording.steps.append(step)
        return step

    def finish(
        self,
        *,
        notes: str = "",
        metadata: dict[str, object] | None = None,
    ) -> LearnedWorkflow:
        recording = self._recording
        if recording is None:
            raise RuntimeError("No learning session is active.")

        workflow = LearnedWorkflow(
            workflow_id=recording.workflow_id,
            name=recording.name,
            application=recording.application,
            trigger=recording.trigger,
            steps=tuple(recording.steps),
            notes=notes,
            metadata=dict(metadata or {}),
        )
        self._recording = None
        return workflow

    def discard(self) -> None:
        self._recording = None
