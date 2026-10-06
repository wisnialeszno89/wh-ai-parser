from __future__ import annotations

from collections.abc import Callable

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_observer import HumanActionObserver
from app.agent.learning.learning_session import LearningSession
from app.agent.perception.screen_scene import ScreenScene


SceneProvider = Callable[[], ScreenScene | None]


class LearningObservationCoordinator:
    """
    Bridges a platform input observer with LearningSession.

    The coordinator captures the current semantic scene before interpreting
    a human event and refreshes it afterwards. The concrete platform observer
    never needs to know how the application is perceived.
    """

    def __init__(
        self,
        *,
        session: LearningSession,
        observer: HumanActionObserver,
        scene_provider: SceneProvider,
    ) -> None:
        self.session = session
        self.observer = observer
        self.scene_provider = scene_provider

    def start(self) -> None:
        if not self.session.is_active:
            raise RuntimeError("Learning session is not active.")

        scene = self.scene_provider()
        if scene is None:
            raise RuntimeError(
                "A semantic scene is required before learning can start."
            )

        self.session.observe_before(scene)

        self.observer.start(
            self._handle_event
        )

    def stop(self) -> None:
        self.observer.stop()

    def _handle_event(
        self,
        event: HumanActionEvent,
    ) -> None:
        scene_before = self.session.before_scene
        if scene_before is None:
            scene_before = self.scene_provider()

        if scene_before is None:
            return

        recorded = self.session.record_human_event(
            event=event,
            scene_before=scene_before,
        )

        if not recorded:
            return

        scene_after = self.scene_provider()
        if scene_after is not None:
            self.session.observe_before(
                scene_after
            )
