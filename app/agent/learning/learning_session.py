from __future__ import annotations

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_interpreter import HumanActionInterpreter
from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.learning.learning_recorder import LearningRecorder
from app.agent.learning.semantic_snapshot import SemanticSnapshot
from app.agent.perception.screen_scene import ScreenScene


class LearningSession:
    """
    Coordinates observation of a human demonstration.

    The platform input layer supplies events. This class observes the scene
    before and after an interpreted event and records a semantic transition.
    """

    def __init__(
        self,
        *,
        recorder: LearningRecorder | None = None,
        interpreter: HumanActionInterpreter | None = None,
    ) -> None:
        self.recorder = recorder or LearningRecorder()
        self.interpreter = interpreter or HumanActionInterpreter()
        self._before_scene: ScreenScene | None = None

    @property
    def is_active(self) -> bool:
        return self.recorder.is_recording

    def start(
        self,
        *,
        workflow_id: str,
        name: str,
        trigger: str,
        application: str | None = None,
        scene: ScreenScene | None = None,
    ) -> None:
        self.recorder.start(
            workflow_id=workflow_id,
            name=name,
            trigger=trigger,
            application=application,
        )
        self._before_scene = scene

    def observe_before(
        self,
        scene: ScreenScene,
    ) -> None:
        if not self.is_active:
            raise RuntimeError("No learning session is active.")
        self._before_scene = scene

    def record_human_event(
        self,
        *,
        event: HumanActionEvent,
        scene_before: ScreenScene | None = None,
        scene_after: ScreenScene | None = None,
        notes: str = "",
    ) -> bool:
        if not self.is_active:
            raise RuntimeError("No learning session is active.")

        before = scene_before or self._before_scene
        if before is None:
            return False

        action = self.interpreter.interpret(
            event=event,
            scene=before,
        )
        if action is None:
            return False

        self.recorder.record_step(
            action=action,
            before=SemanticSnapshot.from_scene(before),
            after=(
                SemanticSnapshot.from_scene(scene_after)
                if scene_after is not None
                else None
            ),
            notes=notes,
        )

        self._before_scene = scene_after or before
        return True

    def finish(
        self,
        *,
        notes: str = "",
        metadata: dict[str, object] | None = None,
    ) -> LearnedWorkflow:
        workflow = self.recorder.finish(
            notes=notes,
            metadata=metadata,
        )
        self._before_scene = None
        return workflow

    def discard(self) -> None:
        self.recorder.discard()
        self._before_scene = None
