from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.window_model.dependency_planner import DependencyPlanner
from app.window_model.diff import WindowChangeType, diff_models
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


@dataclass(frozen=True)
class SemanticExecutionResult:
    status: str
    executed: tuple[str, ...]
    blocked: tuple[str, ...]
    remaining: tuple[str, ...]


class SemanticExecutionBridge:
    """Bridge semantic construction steps to the existing WindowHub executor."""

    def __init__(self, executor: ActionExecutor) -> None:
        self.executor = executor
        self.dependency_planner = DependencyPlanner()

    def _remember_success(self, step) -> None:
        state = self.executor.context.gui_state
        point = state.last_created_point
        if point is not None:
            state.created_element_points[step.element_id] = point
        state.created_element_sides[step.element_id] = step.side.value
        print(f"[SEMANTIC MEMORY] created={step.element_id} side={step.side.value} point={point}")

    def _prepare_step(self, step) -> None:
        # panel_side is placement state for the next panel. The semantic plan
        # is authoritative when a concrete side is known.
        if step.side is not WindowSide.UNKNOWN and step.side is not WindowSide.CENTER:
            self.executor.context.gui_state.panel_side = step.side.value.lower()
            print(f"[SEMANTIC PLACEMENT] side={step.side.value} element={step.element_id}")

    def execute_next(self, desired: WindowModel, topology: WindowTopology, observed: WindowModel) -> SemanticExecutionResult:
        changes = diff_models(desired, observed)
        pending_ids = {change.element_id for change in changes if change.change == WindowChangeType.ADD}
        if not pending_ids:
            return SemanticExecutionResult("COMPLETE", (), (), ())

        steps = self.dependency_planner.plan(desired, topology)
        for step in steps:
            if step.element_id not in pending_ids:
                continue
            if step.gui_tool == GuiTool.HARDWARE:
                return SemanticExecutionResult("BLOCKED", (), (step.element_id,), tuple(sorted(pending_ids)))

            self._prepare_step(step)
            action = SimpleNamespace(
                intent=GuiIntent.CREATE,
                tool=step.gui_tool,
                semantic_id=step.element_id,
                semantic_side=step.side.value,
            )
            result = self.executor.execute(action)
            if not result.success:
                return SemanticExecutionResult("BLOCKED", (), (step.element_id,), tuple(sorted(pending_ids)))

            self._remember_success(step)
            remaining = tuple(sorted(pending_ids - {step.element_id}))
            return SemanticExecutionResult("PARTIAL" if remaining else "COMPLETE", (step.element_id,), (), remaining)

        return SemanticExecutionResult("NO_PROGRESS", (), (), tuple(sorted(pending_ids)))

    def execute_until_blocked(self, desired: WindowModel, topology: WindowTopology, observed: WindowModel) -> SemanticExecutionResult:
        changes = diff_models(desired, observed)
        pending_ids = {change.element_id for change in changes if change.change == WindowChangeType.ADD}
        if not pending_ids:
            return SemanticExecutionResult("COMPLETE", (), (), ())

        steps = self.dependency_planner.plan(desired, topology)
        executed: list[str] = []
        blocked: list[str] = []
        for step in steps:
            if step.element_id not in pending_ids:
                continue
            if step.gui_tool == GuiTool.HARDWARE:
                blocked.append(step.element_id)
                break
            self._prepare_step(step)
            action = SimpleNamespace(intent=GuiIntent.CREATE, tool=step.gui_tool, semantic_id=step.element_id, semantic_side=step.side.value)
            result = self.executor.execute(action)
            if not result.success:
                blocked.append(step.element_id)
                break
            self._remember_success(step)
            executed.append(step.element_id)

        remaining = tuple(step.element_id for step in steps if step.element_id in pending_ids and step.element_id not in executed)
        status = "BLOCKED" if blocked else ("COMPLETE" if not remaining else "PARTIAL")
        return SemanticExecutionResult(status, tuple(executed), tuple(blocked), remaining)


def _add_cell(model: WindowModel, topology: WindowTopology, side: WindowSide, opening: str) -> None:
    name = side.value.lower()
    index = 0 if side is WindowSide.LEFT else 1
    cell = model.add_element(f"cell_{name}", WindowElementType.MULLION, parent_id="frame", role="CELL")
    sash = model.add_element(f"sash_{name}", WindowElementType.SASH, parent_id=cell.id, opening=opening)
    glass = model.add_element(f"glass_{name}", WindowElementType.GLASS, parent_id=sash.id, panes=3)
    hardware = model.add_element(f"hardware_{name}", WindowElementType.HARDWARE, parent_id=sash.id, system="unknown")
    topology.add(cell, side=side, position_index=index, role="CELL")
    topology.add(sash, side=side, position_index=index, opening=opening)
    topology.add(glass, side=side, position_index=index)
    topology.add(hardware, side=side, position_index=index)


def single_cell_left_target() -> tuple[WindowModel, WindowTopology]:
    model = WindowModel(properties={"width": 900, "height": 1200, "cells": 1})
    frame = model.add_element("frame", WindowElementType.FRAME)
    topology = WindowTopology()
    topology.add(frame, side=WindowSide.CENTER, role="FRAME")
    _add_cell(model, topology, WindowSide.LEFT, "left")
    return model, topology


def two_cell_target() -> tuple[WindowModel, WindowTopology]:
    model = WindowModel(properties={"width": 1000, "height": 1000, "cells": 2})
    frame = model.add_element("frame", WindowElementType.FRAME)
    topology = WindowTopology()
    topology.add(frame, side=WindowSide.CENTER, role="FRAME")
    _add_cell(model, topology, WindowSide.LEFT, "left")
    _add_cell(model, topology, WindowSide.RIGHT, "right")
    return model, topology
