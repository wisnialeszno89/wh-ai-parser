"""Human-first control-panel state machine, independent of Tk and Windows.

This controller owns one arbiter; an unconnected panel is safe by default.
It cannot start a WindowHub job, record a demonstration or assert success.
A future trusted Windows host may connect a verified observation callback.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from app.agent.runtime.navimind_local_input_arbiter import (
    ActionPermit, InputOwner, LocalInputArbiter,
)


class PanelMode(str, Enum):
    HUMAN = "human"
    RESUME_PENDING = "resume_pending"
    AGENT_READY = "agent_ready"
    LEARNING = "learning"
    STOPPED = "stopped"


@dataclass(frozen=True)
class PanelSnapshot:
    mode: PanelMode
    title: str
    detail: str
    human_controls: bool
    connected: bool
    can_resume: bool
    can_takeover: bool
    can_stop: bool
    can_learn: bool
    document_label: str
    revision: int


class NaviMindPanelController:
    """Explicit, reversible UI commands; no hidden desktop actions.

    resume() never grants an input permit. A trusted host must independently
    observe the exact document and call confirm_verified_resume(). The panel
    itself never accepts an unverified document id typed by the operator.
    """

    def __init__(self, arbiter: LocalInputArbiter | None = None) -> None:
        self.arbiter = arbiter or LocalInputArbiter()
        # Human ownership from the first render: a panel on its own is not
        # permission for a previously running background process to click.
        if self.arbiter.owner == InputOwner.AGENT:
            self.arbiter.takeover()
        self.mode = PanelMode.HUMAN
        self.connected = False
        self.document_label = "Brak połączonego zadania"
        self.revision = 0
        self._active_permit: ActionPermit | None = None
        self._listeners: list[Callable[[PanelSnapshot], None]] = []

    def subscribe(self, listener: Callable[[PanelSnapshot], None]) -> None:
        self._listeners.append(listener)
        listener(self.snapshot())

    def _notify(self) -> PanelSnapshot:
        self.revision += 1
        view = self.snapshot()
        for callback in tuple(self._listeners):
            callback(view)
        return view

    def snapshot(self) -> PanelSnapshot:
        status = {
            PanelMode.HUMAN: ("Sterowanie ręczne", "Możesz swobodnie korzystać z komputera."),
            PanelMode.RESUME_PENDING: ("Oczekiwanie na weryfikację",
                                       "Po wznowieniu trzeba ponownie odczytać program i dokument."),
            PanelMode.AGENT_READY: ("Gotowy do pracy",
                                    "Dokument sprawdzony. Działania nadal podlegają zabezpieczeniom V2."),
            PanelMode.LEARNING: ("Tryb nauki", "Pokaż czynność ręcznie. Nagrywanie nie jest jeszcze podłączone."),
            PanelMode.STOPPED: ("Zadanie zatrzymane", "Tego zadania nie można wznowić starym planem."),
        }[self.mode]
        return PanelSnapshot(
            mode=self.mode, title=status[0], detail=status[1],
            human_controls=self.arbiter.owner == InputOwner.HUMAN,
            connected=self.connected,
            can_resume=self.mode in (PanelMode.HUMAN, PanelMode.LEARNING),
            can_takeover=self.mode in (PanelMode.RESUME_PENDING, PanelMode.AGENT_READY),
            can_stop=self.mode != PanelMode.STOPPED,
            can_learn=self.mode == PanelMode.HUMAN,
            document_label=self.document_label,
            revision=self.revision,
        )

    def takeover(self) -> PanelSnapshot:
        if self.mode == PanelMode.STOPPED:
            return self.snapshot()
        if self.arbiter.owner != InputOwner.HUMAN:
            self.arbiter.takeover()
        self.mode = PanelMode.HUMAN
        self._active_permit = None
        return self._notify()

    def resume(self) -> PanelSnapshot:
        if self.mode not in (PanelMode.HUMAN, PanelMode.LEARNING):
            return self.snapshot()
        if self.arbiter.owner != InputOwner.HUMAN:
            # Fail closed if an external host changed ownership unexpectedly.
            self.arbiter.takeover()
        self.arbiter.release()
        self._active_permit = None
        self.mode = PanelMode.RESUME_PENDING
        return self._notify()

    def confirm_verified_resume(
        self, *, verified_document_key: str, verified_from_fresh_scene: bool,
    ) -> PanelSnapshot:
        """Trusted integration API only, NOT an end-user input control."""
        if (self.mode != PanelMode.RESUME_PENDING
                or not self.connected
                or verified_from_fresh_scene is not True
                or not isinstance(verified_document_key, str)
                or not verified_document_key.strip()):
            raise ValueError("fresh_verified_connected_document_required")
        if self.arbiter.owner != InputOwner.AGENT:
            raise ValueError("agent_not_owner")
        permit = self.arbiter.observe_document(verified_document_key)
        self._active_permit = permit
        self.mode = PanelMode.AGENT_READY
        self.document_label = "Dokument zweryfikowany"
        return self._notify()

    def training(self) -> PanelSnapshot:
        if self.mode != PanelMode.HUMAN:
            return self.snapshot()
        self._active_permit = None
        self.mode = PanelMode.LEARNING
        return self._notify()

    def stop(self) -> PanelSnapshot:
        if self.mode == PanelMode.STOPPED:
            return self.snapshot()
        if self.arbiter.owner != InputOwner.HUMAN:
            self.arbiter.takeover()
        else:
            self.arbiter.invalidate_observation()
        self._active_permit = None
        self.mode = PanelMode.STOPPED
        return self._notify()

    def connect_host(self) -> PanelSnapshot:
        """Trusted host opt-in, not automatic connection to Windows."""
        if self.mode == PanelMode.STOPPED:
            raise ValueError("task_already_stopped")
        self.connected = True
        return self._notify()

    def current_permit(self) -> ActionPermit | None:
        if (self.mode == PanelMode.AGENT_READY and self.connected
                and self._active_permit is not None
                and self.arbiter.permit_current(self._active_permit)):
            return self._active_permit
        return None
