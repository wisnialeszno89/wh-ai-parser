from __future__ import annotations

from collections.abc import Callable
import queue
import threading

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_observer import HumanActionObserver
from app.agent.learning.learning_session import LearningSession
from app.agent.perception.screen_scene import ScreenScene


SceneProvider = Callable[[], ScreenScene | None]


class LearningObservationCoordinator:
    """
    Bridges a platform input observer with LearningSession.

    Input events are queued so a slow perception cycle cannot block the
    platform mouse observer and cause later human interactions to be missed.
    Events are interpreted sequentially against the latest known semantic
    scene.
    """

    _STOP = object()

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
        self._queue: queue.Queue[
            HumanActionEvent | object
        ] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        if not self.session.is_active:
            raise RuntimeError("Learning session is not active.")

        # The controller may already have captured the initial scene. Do not
        # take a second observation here because the UI can legitimately
        # change between those two calls, which would make the first human
        # action be interpreted against the wrong state.
        scene = self.session.before_scene
        if scene is None:
            scene = self.scene_provider()

        if scene is None:
            raise RuntimeError(
                "A semantic scene is required before learning can start."
            )

        self.session.observe_before(scene)

        self._running = True
        self._worker = threading.Thread(
            target=self._process_events,
            name="agent-learning-observation-coordinator",
            daemon=True,
        )
        self._worker.start()

        try:
            self.observer.start(
                self._handle_event
            )
        except Exception:
            self._running = False
            self._queue.put(self._STOP)
            self._worker.join(timeout=1.0)
            self._worker = None
            raise

    def stop(self) -> None:
        self.observer.stop()

        if self._running:
            self._running = False
            self._queue.put(self._STOP)

        worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout=5.0)

        self._worker = None

    def _handle_event(
        self,
        event: HumanActionEvent,
    ) -> None:
        self._queue.put(event)

    def _process_events(self) -> None:
        while True:
            item = self._queue.get()

            if item is self._STOP:
                self._queue.task_done()
                return

            assert isinstance(item, HumanActionEvent)

            try:
                self._process_event(item)
            finally:
                self._queue.task_done()

    def _process_event(
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
