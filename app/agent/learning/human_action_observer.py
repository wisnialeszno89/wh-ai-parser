from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from app.agent.learning.human_action_event import HumanActionEvent


HumanActionCallback = Callable[[HumanActionEvent], None]


class HumanActionObserver(ABC):
    """
    Platform-neutral source of transient human interaction events.

    Observers may use physical coordinates internally to interpret an event,
    but the observer itself never decides what should be persisted.
    """

    @abstractmethod
    def start(
        self,
        callback: HumanActionCallback,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError
