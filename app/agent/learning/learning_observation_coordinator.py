from __future__ import annotations

from collections.abc import Callable
import queue
import threading
import time

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_observer import HumanActionObserver
from app.agent.learning.learning_session import LearningSession
from app.agent.learning.semantic_snapshot import SemanticSnapshot
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

            # The STOP sentinel is queued after all human events already
            # captured by the observer. Drain the queue before returning so
            # a slow post-action semantic observation cannot be lost when
            # the user finishes the demonstration.
            self._queue.join()

        worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout=1.0)

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

    _POST_EVENT_SETTLE_TIMEOUT_SECONDS = 1.0
    _POST_EVENT_POLL_INTERVAL_SECONDS = 0.05
    _INTERPRET_RETRY_COUNT = 4

    def _process_event(
        self,
        event: HumanActionEvent,
    ) -> None:
        scene_before = self.session.before_scene
        if scene_before is None:
            scene_before = self.scene_provider()

        if scene_before is None:
            return

        # A human action can change the UI slightly after the physical click.
        # Wait for a semantic scene transition before recording the post-state
        # so the next event is interpreted against the state the human saw.
        scene_after = self._observe_after_event(scene_before)

        recorded = self.session.record_human_event(
            event=event,
            scene_before=scene_before,
            scene_after=scene_after,
        )

        # A queued event may overtake the previous slow semantic observation.
        # When the stored before-scene cannot interpret the event, refresh the
        # current semantic scene and retry a few times instead of dropping the
        # human action.
        for _ in range(self._INTERPRET_RETRY_COUNT):
            if recorded:
                break

            refreshed = self.scene_provider()
            if refreshed is None:
                time.sleep(self._POST_EVENT_POLL_INTERVAL_SECONDS)
                continue

            scene_before = refreshed
            scene_after = self._observe_after_event(scene_before)
            recorded = self.session.record_human_event(
                event=event,
                scene_before=scene_before,
                scene_after=scene_after,
            )

        if not recorded:
            return

        self.session.observe_before(
            scene_after or scene_before
        )

    def _observe_after_event(
        self,
        scene_before: ScreenScene,
    ) -> ScreenScene | None:
        initial_fingerprint = self._scene_fingerprint(
            scene_before
        )

        deadline = (
            time.monotonic()
            + self._POST_EVENT_SETTLE_TIMEOUT_SECONDS
        )

        latest_scene = None
        previous_fingerprint = None
        stable_count = 0

        while time.monotonic() < deadline:
            time.sleep(
                self._POST_EVENT_POLL_INTERVAL_SECONDS
            )

            scene = self.scene_provider()
            if scene is None:
                continue

            latest_scene = scene
            fingerprint = self._scene_fingerprint(scene)

            if fingerprint == previous_fingerprint:
                stable_count += 1
            else:
                previous_fingerprint = fingerprint
                stable_count = 1

            if (
                fingerprint != initial_fingerprint
                and stable_count >= 2
            ):
                return scene

        return latest_scene or scene_before

    @staticmethod
    def _scene_fingerprint(
        scene: ScreenScene,
    ) -> tuple[object, ...]:
        snapshot = SemanticSnapshot.from_scene(scene)

        return (
            snapshot.application,
            snapshot.window_title,
            snapshot.active_document,
            tuple(
                (
                    item.get("kind"),
                    item.get("label"),
                    item.get("interaction_capability"),
                    item.get("current_value"),
                    item.get("document_scope"),
                    item.get("uia_tab_scope"),
                    item.get("uia_document_tab_selected"),
                )
                for item in snapshot.elements
            ),
        )
