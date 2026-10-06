from __future__ import annotations

from dataclasses import dataclass
import time

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_observer import (
    HumanActionCallback,
    HumanActionObserver,
)
from app.agent.perception.screen_scene import ScreenScene


_TEXT_CONTROL_KINDS = frozenset({
    "edit",
    "textbox",
    "input",
    "combobox",
})


@dataclass
class _FieldObservation:
    kind: str
    target: str
    value: str
    document_scope: str | None
    tab_scope: str | None
    focused: bool | None


@dataclass
class _FieldState:
    last_value: str
    pending_value: str | None = None
    pending_since: float | None = None


class SemanticTextInputTracker:
    """
    Infers human text entry from semantic field state changes.

    It never observes keyboard scan codes, pressed keys or clipboard
    contents. A text action is emitted only after one semantic field has
    changed and remained stable for the configured settle period.
    """

    def __init__(self, *, settle_seconds: float = 0.30) -> None:
        if settle_seconds < 0:
            raise ValueError("settle_seconds must be non-negative.")

        self.settle_seconds = settle_seconds
        self._states: dict[
            tuple[str, str, str | None, str | None],
            _FieldState,
        ] = {}

    def reset(self, scene: ScreenScene) -> None:
        self._states = {
            key: _FieldState(last_value=field.value)
            for key, field in self._collect_fields(scene).items()
        }

    def observe(
        self,
        scene: ScreenScene,
        *,
        now: float | None = None,
    ) -> tuple[HumanActionEvent, ...]:
        current_time = (
            time.monotonic()
            if now is None
            else float(now)
        )

        fields = self._collect_fields(scene)

        active_keys = set(fields)
        for key in tuple(self._states):
            if key not in active_keys:
                del self._states[key]

        changed_keys: list[
            tuple[str, str, str | None, str | None]
        ] = []

        for key, field in fields.items():
            state = self._states.get(key)

            if state is None:
                self._states[key] = _FieldState(
                    last_value=field.value
                )
                continue

            if field.value == state.last_value:
                state.pending_value = None
                state.pending_since = None
                continue

            changed_keys.append(key)

            if state.pending_value != field.value:
                state.pending_value = field.value
                state.pending_since = current_time

        events: list[HumanActionEvent] = []

        for key in changed_keys:
            field = fields[key]
            state = self._states[key]

            if (
                state.pending_value is None
                or state.pending_since is None
                or current_time - state.pending_since < self.settle_seconds
            ):
                continue

            if (
                field.focused is not True
                and len(changed_keys) != 1
            ):
                continue

            value = state.pending_value

            events.append(
                HumanActionEvent(
                    action_type="write_text",
                    value=value,
                    metadata={
                        "event_uia_name": field.target,
                        "event_uia_control_type": field.kind,
                        "event_uia_source": "semantic_text_input",
                        "semantic_text_input": True,
                        "semantic_text_input_mode": "replace",
                        "semantic_text_document_scope": (
                            field.document_scope
                        ),
                        "semantic_text_tab_scope": field.tab_scope,
                    },
                )
            )

            state.last_value = value
            state.pending_value = None
            state.pending_since = None

        return tuple(events)

    @staticmethod
    def _collect_fields(
        scene: ScreenScene,
    ) -> dict[
        tuple[str, str, str | None, str | None],
        _FieldObservation,
    ]:
        grouped: dict[
            tuple[str, str, str | None, str | None],
            list[_FieldObservation],
        ] = {}

        for element in scene.elements:
            kind = element.kind.strip().casefold()
            if kind not in _TEXT_CONTROL_KINDS:
                continue

            if not isinstance(element.label, str):
                continue

            target = element.label.strip()
            if not target:
                continue

            metadata = element.metadata or {}
            raw_value = metadata.get("current_value")

            if isinstance(raw_value, str):
                value = raw_value
            elif raw_value is None:
                value = ""
            else:
                value = str(raw_value)

            document_scope = metadata.get("document_scope")
            if not isinstance(document_scope, str):
                document_scope = None

            tab_scope = metadata.get("uia_tab_scope")
            if not isinstance(tab_scope, str):
                tab_scope = None

            focused = metadata.get("uia_focused")
            if not isinstance(focused, bool):
                focused = None

            key = (
                kind,
                target.casefold(),
                document_scope,
                tab_scope,
            )

            grouped.setdefault(key, []).append(
                _FieldObservation(
                    kind=kind,
                    target=target,
                    value=value,
                    document_scope=document_scope,
                    tab_scope=tab_scope,
                    focused=focused,
                )
            )

        return {
            key: values[0]
            for key, values in grouped.items()
            if len(values) == 1
        }


class SemanticTextInputObserver(HumanActionObserver):
    """
    Background observer for semantic text-entry changes.

    The observer uses only the supplied semantic scene provider. It has no
    keyboard hook and does not receive raw keystrokes.
    """

    def __init__(
        self,
        *,
        scene_provider,
        poll_interval_seconds: float = 0.05,
        settle_seconds: float = 0.30,
        tracker: SemanticTextInputTracker | None = None,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError(
                "poll_interval_seconds must be positive."
            )

        self.scene_provider = scene_provider
        self.poll_interval_seconds = poll_interval_seconds
        self.tracker = (
            tracker
            if tracker is not None
            else SemanticTextInputTracker(
                settle_seconds=settle_seconds
            )
        )
        self._stop_event = None
        self._thread = None
        self._callback: HumanActionCallback | None = None

    def start(self, callback: HumanActionCallback) -> None:
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError(
                "Semantic text input observer is already running."
            )

        initial_scene = self.scene_provider()
        if initial_scene is None:
            raise RuntimeError(
                "A semantic scene is required before text observation can start."
            )

        import threading

        self.tracker.reset(initial_scene)
        self._callback = callback
        self._stop_event = threading.Event()

        self._thread = threading.Thread(
            target=self._run,
            name="agent-semantic-text-observer",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        stop_event = self._stop_event
        if stop_event is not None:
            stop_event.set()

        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

        self._thread = None
        self._stop_event = None
        self._callback = None

    def _run(self) -> None:
        stop_event = self._stop_event
        if stop_event is None:
            return

        while not stop_event.is_set():
            try:
                scene = self.scene_provider()
            except Exception:
                scene = None

            if scene is not None:
                events = self.tracker.observe(scene)
                callback = self._callback

                if callback is not None:
                    for event in events:
                        callback(event)

            stop_event.wait(self.poll_interval_seconds)
