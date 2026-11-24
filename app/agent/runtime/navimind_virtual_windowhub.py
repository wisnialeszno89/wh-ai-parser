"""Offline in-memory WindowHub simulator for NaviMind's mission planner.

NOT an emulator of the actual Winkhaus application. It models business-level
position operations and independent in-memory readback only, allowing Linux
Codespaces to exercise mission flow and recovery without native Windows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.agent.offers.windowhub_commercial_quote_routes import (
    QuoteCapabilities, plan_commercial_quote,
)
from app.agent.runtime.navimind_mission_coordinator import (
    MissionAction, MissionIntent, MissionScene, PositionReadback, PositionTask,
    mission_progress_summary, next_mission_intent,
)
from app.agent.runtime.portable_editor_skills import EditorTarget


@dataclass
class VirtualPosition:
    route: str
    description: str | None = None
    image_reference: str | None = None
    unit_price: str | None = None


@dataclass
class VirtualWindowHub:
    """A deliberately small model of ONE already open, unsaved offer."""
    document_id: str
    capabilities: QuoteCapabilities
    positions: dict[str, VirtualPosition] = field(default_factory=dict)
    active_position_id: str | None = None
    observed_application: str = "WindowHub"
    stale: bool = False
    attempted_actions: list[tuple[str, str]] = field(default_factory=list)
    injected_noops: set[tuple[str, str]] = field(default_factory=set)
    saved: bool = False
    sent: bool = False

    def scene(self) -> MissionScene:
        active = self.active_position_id
        editor = None
        if active is not None and active in self.positions:
            editor = EditorTarget(
                "WindowHub", self.document_id, active, "description",
                unique=True, editable=True,
                supports_images=self.capabilities.image_insert_supported,
                live_observed=not self.stale,
            )
        return MissionScene(
            application=self.observed_application,
            document_id=self.document_id,
            document_identity_verified=bool(self.document_id),
            fresh=not self.stale,
            active_position_id=active,
            quote_capabilities=self.capabilities,
            editor_target=editor,
        )

    def observe(self, tasks: tuple[PositionTask, ...]) -> tuple[PositionReadback, ...]:
        """Recompute proof from actual virtual state, never from action claims."""
        result = []
        for task in tasks:
            position = self.positions.get(task.position_id)
            if position is None:
                continue
            plan = plan_commercial_quote(task.request, self.capabilities, task.technical)
            result.append(PositionReadback(
                position_id=task.position_id,
                document_id=self.document_id,
                fresh=not self.stale,
                exact_position=True,
                created_verified=position.route == plan.route.value,
                description_verified=position.description == plan.proposed_description,
                image_verified=(
                    bool(task.request.image_reference)
                    and plan.image_ready
                    and plan.image_reference is not None
                    and position.image_reference is not None
                    and position.image_reference == plan.image_reference
                ),
                price_verified=(
                    position.unit_price == plan.manual_unit_price
                    and plan.manual_unit_price is not None
                ),
            ))
        return tuple(result)

    def apply(self, intent: MissionIntent, tasks: tuple[PositionTask, ...]) -> bool:
        """Process one fully grounded simulated proposal. No real GUI writes."""
        if not intent.requires_v2_executor or intent.position_id is None:
            return False
        matches = [t for t in tasks if t.position_id == intent.position_id]
        if len(matches) != 1 or self.stale or self.observed_application != "WindowHub":
            return False
        task = matches[0]
        plan = plan_commercial_quote(task.request, self.capabilities, task.technical)
        if intent.proposed_route is not None and intent.proposed_route != plan.route:
            return False
        key = (task.position_id, intent.action.value)
        self.attempted_actions.append(key)
        if key in self.injected_noops:
            self.injected_noops.remove(key)
            return False
        position = self.positions.get(task.position_id)
        if intent.action == MissionAction.CREATE_POSITION:
            if position is not None or plan.route.value == "manual_review":
                return False
            self.positions[task.position_id] = VirtualPosition(route=plan.route.value)
            self.active_position_id = task.position_id
            return True
        if position is None or self.active_position_id != task.position_id:
            return False
        if intent.action == MissionAction.WRITE_DESCRIPTION:
            if intent.description != plan.proposed_description:
                return False
            position.description = intent.description
            return True
        if intent.action == MissionAction.INSERT_IMAGE:
            if not plan.image_ready or intent.image_reference != plan.image_reference:
                return False
            position.image_reference = intent.image_reference
            return True
        if intent.action == MissionAction.SET_MANUAL_PRICE:
            if plan.manual_unit_price is None or intent.price != plan.manual_unit_price:
                return False
            position.unit_price = intent.price
            return True
        return False

    def activate(self, position_id: str) -> bool:
        if position_id not in self.positions:
            return False
        self.active_position_id = position_id
        return True


@dataclass(frozen=True)
class SimulationTrace:
    actions: tuple[str, ...]
    terminal_reason: str
    finished: bool
    summary: dict


def run_virtual_mission(
    tasks: tuple[PositionTask, ...], environment: VirtualWindowHub,
    *,
    max_cycles: int = 80,
    auto_activate: bool = True,
) -> SimulationTrace:
    """Exercise coordinator, fake executor, re-observation, failure handling.

    Does not turn non-progress into a success. For an injected no-op, revisiting
    an unchanged state escalates for review instead of making a blind retry.
    """
    if max_cycles < 1:
        raise ValueError("max_cycles_must_be_positive")
    attempted_without_progress: set[str] = set()
    trace: list[str] = []
    for _ in range(max_cycles):
        before = environment.observe(tasks)
        scene = environment.scene()
        intent = next_mission_intent(
            tasks, scene, before,
            attempted_without_progress=tuple(attempted_without_progress),
        )
        trace.append(intent.action.value + ":" + str(intent.position_id) + ":" + intent.reason)
        if intent.action == MissionAction.COMPLETE:
            summary = mission_progress_summary(tasks, environment.scene(), environment.observe(tasks))
            complete = summary["all_position_requirements_verified"]
            return SimulationTrace(tuple(trace), intent.reason, complete, summary)
        if intent.action == MissionAction.REVIEW:
            return SimulationTrace(
                tuple(trace), intent.reason, False,
                mission_progress_summary(tasks, scene, before),
            )
        if intent.action == MissionAction.OBSERVE:
            if (auto_activate and intent.position_id is not None
                    and intent.reason == "activate_exact_position_before_editing"
                    and environment.activate(intent.position_id)):
                continue
            return SimulationTrace(
                tuple(trace), intent.reason, False,
                mission_progress_summary(tasks, scene, before),
            )
        applied = environment.apply(intent, tasks)
        if not applied:
            # Prevent second ungrounded attempt of same action on same field.
            attempted_without_progress.add(str(intent.position_id) + ":" + intent.action.value)
    return SimulationTrace(
        tuple(trace), "max_cycles_exhausted", False,
        mission_progress_summary(tasks, environment.scene(), environment.observe(tasks)),
    )
