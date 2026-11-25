"""Chat-to-V2 mission bridge: one goal, one pinned revision, verified progress.

This host-side coordinator does not use user/model-provided Python names,
desktop coordinates, commands or filesystem paths. Model classification only
selects a trusted capability. All GUI input must go through the shared host's
permitted V2 single-step executor. The default entry point thinks without
clicking; an explicit operator-controlled resume and live flags are required
for act mode. No saving/sending/persistent business commits.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
from uuid import uuid4
from typing import Callable, Any


class WorkStage(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    THINKING = "thinking"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    REVIEW = "review"
    COMPLETED_UNVERIFIED = "completed_unverified"


@dataclass(frozen=True)
class WorkMission:
    task_id: str
    revision: int
    message_id: int
    goal: str
    document_key: str
    stage: WorkStage
    cycles: int = 0
    reason: str = ""
    suggested_action: str = ""


class WorkMissionCoordinator:
    """Single latest mission, no native operations in this state machine.

    Events are accepted only for the exact current user message/revision.
    A new human message makes previous model replies and actions stale.
    """

    def __init__(self, chat, *, max_cycles: int = 8):
        if type(max_cycles) is not int or not 1 <= max_cycles <= 20:
            raise ValueError("invalid_mission_budget")
        self.chat = chat
        self.max_cycles = max_cycles
        self._lock = RLock()
        self._mission: WorkMission | None = None

    def current(self) -> WorkMission | None:
        with self._lock:
            return self._mission

    def _is_current(self, item: WorkMission) -> bool:
        snapshot = self.chat.snapshot()
        return (
            snapshot.mission_revision == item.revision
            and any(
                msg.message_id == item.message_id
                and msg.mission_revision == item.revision
                and msg.text == item.goal
                and getattr(msg.role, "value", msg.role) == "human"
                for msg in snapshot.messages
            )
        )

    def queue_current(self) -> WorkMission | None:
        """Only an actual current human turn supplies the executable goal."""
        with self._lock:
            snapshot = self.chat.snapshot()
            humans = [
                m for m in snapshot.messages
                if getattr(m.role, "value", m.role) == "human"
                and m.mission_revision == snapshot.mission_revision
            ]
            if not humans:
                return None
            human = humans[-1]
            if not human.text.strip() or len(human.text) > 4000:
                return None
            if (self._mission is not None
                    and self._mission.message_id == human.message_id
                    and self._is_current(self._mission)):
                return self._mission
            self._mission = WorkMission(
                task_id="work-" + uuid4().hex[:16],
                revision=human.mission_revision,
                message_id=human.message_id,
                goal=human.text,
                document_key=self.chat.document_key,
                stage=WorkStage.QUEUED,
            )
            return self._mission

    def transition(
        self, task_id: str, stage: WorkStage, *,
        reason: str = "", suggested_action: str = "",
        count_step: bool = False,
    ) -> WorkMission | None:
        with self._lock:
            item = self._mission
            if (item is None or item.task_id != task_id
                    or not self._is_current(item)):
                return None
            if count_step and item.cycles >= self.max_cycles:
                stage = WorkStage.REVIEW
                reason = "mission_action_budget_exhausted"
                count_step = False
            from dataclasses import replace
            self._mission = replace(
                item, stage=stage,
                reason=reason[:160],
                suggested_action=suggested_action[:80],
                cycles=item.cycles + (1 if count_step else 0),
            )
            return self._mission

    def cancel_stale(self) -> bool:
        with self._lock:
            if self._mission is None or self._is_current(self._mission):
                return False
            self._mission = None
            return True


@dataclass(frozen=True)
class WorkStepResult:
    kind: str
    reason: str
    action: str = ""
    verified: bool = False


def plan_or_execute_windowhub_step(
    *, mission: WorkMission, loop: Any, reasoner: Any, host: Any,
    execute: bool = False,
) -> WorkStepResult:
    """Reuse native V2 world/action contracts for one bounded mission step.

    Caller owns the worker/COM lifecycle. Never retry an uncertain GUI action.
    The model cannot authorize persistence and cannot change mission's goal
    or pinned offer ID. Action is dispatched only through the shared host.
    """
    from app.agent.learning.windowhub_demonstration import stage_of
    from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
    from app.agent.runtime.windowhub_mdi_native_probe import (
        enrich_native_mdi_document_scope,
    )
    from app.agent.runtime.computer_use_v2_action_session import (
        ComputerUseV2ActionSession,
    )
    from app.agent.runtime.windowhub_goal_v2_coordinator import (
        enforce_v2_live_policy,
    )

    if mission.stage not in {
        WorkStage.QUEUED, WorkStage.THINKING, WorkStage.READY,
        WorkStage.PAUSED, WorkStage.EXECUTING,
    }:
        return WorkStepResult("review", "mission_not_ready_for_step")
    if mission.cycles >= 20:
        return WorkStepResult("review", "absolute_cycle_limit")
    if not mission.goal.strip() or not mission.document_key.strip():
        return WorkStepResult("review", "mission_goal_or_document_missing")

    try:
        raw = loop.observe_scene()
        scene = enrich_windowhub_scene(enrich_native_mdi_document_scope(raw))
        stage = stage_of(scene)
    except Exception:
        return WorkStepResult("paused", "windowhub_observation_unavailable")
    if stage is None:
        return WorkStepResult("paused", "windowhub_not_foreground")
    if stage == "order_document":
        return WorkStepResult("review", "order_document_not_authorized")

    prepared = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id=mission.task_id,
        session_id=mission.task_id, goal=mission.goal,
        world_revision=mission.cycles + 1, cycle=mission.cycles,
        max_cycles=20,
    )
    prepared.request_payload["metadata"]["verified_windowhub_stage"] = stage
    try:
        decision = reasoner.reason(prepared.request_payload)
    except Exception:
        decision = None
    if decision is None:
        return WorkStepResult("paused", "v2_reasoner_unavailable")
    if decision.get("decision") == "done":
        return WorkStepResult(
            "review", "model_declared_done_needs_independent_business_readback"
        )
    if (decision.get("decision") != "act"
            or type(decision.get("confidence")) not in (int, float)
            or decision["confidence"] < .80):
        return WorkStepResult("review", "model_needs_salesperson_or_observation")
    try:
        action = prepared.resolve_action_decision(decision)
        enforce_v2_live_policy(scene, action, approved_persistent=False)
    except (ValueError, RuntimeError, KeyError, TypeError):
        return WorkStepResult("review", "proposed_action_failed_local_policy")
    name = action.action.name
    if name not in {"click_screen_element", "write_text"}:
        return WorkStepResult("review", "action_type_not_authorized_for_mission")
    if action.action.requires_confirmation:
        return WorkStepResult("review", "persistent_action_requires_salesperson")

    if not execute:
        return WorkStepResult("ready", "v2_action_locally_validated_not_executed", name)
    # All input routes through a single pinned-offer host and its arbiter.
    # WindowHub must be actively observed for UI writes; silent background
    # control would interfere with the human desktop.
    if (not isinstance(host.expected_offer, str)
            or host.expected_offer != mission.document_key):
        return WorkStepResult("paused", "pinned_offer_mismatch")
    try:
        host.execute_one_verified_v2_action(
            loop, action, approved_persistent=False,
        )
    except Exception:
        # An unverified action may have physically occurred. No blind retry.
        return WorkStepResult("review", "v2_input_blocked_or_postcondition_unverified", name)
    return WorkStepResult("action", "one_native_step_verified_reobserve_next", name, True)


class BackgroundWorkMission:
    """Run planning on a worker thread. UI never waits for V2 network calls.

    Execution is separately requested by the trusted UI when the operator
    has explicitly resumed control for the pinned document.
    """
    def __init__(
        self, coordinator: WorkMissionCoordinator, *, host: Any,
        callback: Callable[[WorkMission, WorkStepResult], None] | None = None,
        loop_factory: Callable[[], Any] | None = None,
        reasoner_factory: Callable[[], Any] | None = None,
    ):
        from concurrent.futures import ThreadPoolExecutor
        self.coordinator = coordinator
        self.host = host
        self.callback = callback
        self.loop_factory = loop_factory
        self.reasoner_factory = reasoner_factory
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="navimind-work")
        self._lock = RLock()
        self._busy = False
        self._closed = False

    def status(self) -> str:
        with self._lock:
            if self._closed:
                return "closed"
            if self._busy:
                return "busy"
        mission = self.coordinator.current()
        return mission.stage.value if mission else "idle"

    def queue_and_plan(self) -> str:
        mission = self.coordinator.queue_current()
        if mission is None:
            return "Nie ma aktualnego polecenia handlowca. Niczego nie uruchomiłem."
        with self._lock:
            if self._closed:
                return "Silnik zadań jest zamknięty."
            if self._busy:
                return "Silnik analizuje już bieżące zadanie."
            self._busy = True
        self._pool.submit(self._work, mission.task_id, False)
        return (
            "Zadanie przyjęte do lokalnego silnika V2. "
            "Sprawdzam aktualny ekran i możliwy następny krok. "
            "Nie klikam, nie zapisuję ani nie wysyłam oferty."
        )

    def execute_one_authorized_step(self) -> bool:
        """Only trusted local UI invokes this after a verified operator resume."""
        mission = self.coordinator.current()
        if mission is None or mission.stage not in {
            WorkStage.READY, WorkStage.PAUSED,
        }:
            return False
        if self.host.controller.current_permit() is None:
            return False
        with self._lock:
            if self._closed or self._busy:
                return False
            self._busy = True
        self._pool.submit(self._work, mission.task_id, True)
        return True

    def _work(self, task_id: str, execute: bool) -> None:
        com = False
        try:
            try:
                import pythoncom
                pythoncom.CoInitialize()
                com = True
            except ImportError:
                pass
            mission = self.coordinator.current()
            if mission is None or mission.task_id != task_id:
                return
            current = self.coordinator.transition(
                task_id, WorkStage.EXECUTING if execute else WorkStage.THINKING
            )
            if current is None:
                return
            from app.agent.runtime.windows_desktop_agent_control_loop import (
                create_windows_desktop_agent_control_loop,
            )
            from app.agent.reasoning.navimind_task_reasoner_v2 import (
                NaviMindTaskReasonerV2,
            )
            loop = (
                self.loop_factory() if self.loop_factory
                else create_windows_desktop_agent_control_loop()
            )
            reasoner = (
                self.reasoner_factory() if self.reasoner_factory
                else NaviMindTaskReasonerV2()
            )
            result = plan_or_execute_windowhub_step(
                mission=current, loop=loop, reasoner=reasoner,
                host=self.host, execute=execute,
            )
            target = {
                "ready": WorkStage.READY,
                "action": WorkStage.PAUSED,
                "paused": WorkStage.PAUSED,
                "review": WorkStage.REVIEW,
            }.get(result.kind, WorkStage.REVIEW)
            updated = self.coordinator.transition(
                task_id, target,
                reason=result.reason,
                suggested_action=result.action,
                count_step=execute and result.kind == "action",
            )
            if updated is not None and self.callback is not None:
                self.callback(updated, result)
        except Exception:
            updated = self.coordinator.transition(
                task_id, WorkStage.PAUSED, reason="local_work_runtime_unavailable"
            )
            if updated is not None and self.callback:
                self.callback(
                    updated,
                    WorkStepResult("paused", "local_work_runtime_unavailable"),
                )
        finally:
            if com:
                import pythoncom
                pythoncom.CoUninitialize()
            with self._lock:
                self._busy = False

    def close(self) -> None:
        with self._lock:
            self._closed = True
        self._pool.shutdown(wait=False, cancel_futures=True)
