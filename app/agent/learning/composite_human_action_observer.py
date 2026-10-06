from __future__ import annotations

from app.agent.learning.human_action_observer import (
    HumanActionCallback,
    HumanActionObserver,
)


class CompositeHumanActionObserver(HumanActionObserver):
    """
    Fan-in adapter that exposes multiple human-input observers as one source.

    Each child remains responsible for its own platform or semantic evidence.
    The coordinator receives one unified stream of HumanActionEvent objects.
    """

    def __init__(
        self,
        *,
        observers: tuple[HumanActionObserver, ...],
    ) -> None:
        if not observers:
            raise ValueError(
                "At least one human action observer is required."
            )

        self.observers = observers

    def start(self, callback: HumanActionCallback) -> None:
        started: list[HumanActionObserver] = []

        try:
            for observer in self.observers:
                observer.start(callback)
                started.append(observer)
        except Exception:
            for observer in reversed(started):
                try:
                    observer.stop()
                except Exception:
                    pass
            raise

    def stop(self) -> None:
        for observer in reversed(self.observers):
            observer.stop()
