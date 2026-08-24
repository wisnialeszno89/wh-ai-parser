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

    def execute_next(
        self,
        desired: WindowModel,
        topology: WindowTopology,
        observed: WindowModel,
    ) -> SemanticExecutionResult:
        changes = diff_models(desired, observed)
        pending_ids = {
            change.element_id
            for change in changes
            if change.change == WindowChangeType.ADD
        }
        if not pending_ids:
            return SemanticExecutionResult("COMPLETE", (), (), ())

        steps = self.dependency_planner.plan(desired, topology)
        for step in steps:
            if step.element_id not in pending_ids:
                continue
            if step.gui_tool == GuiTool.HARDWARE:
                return SemanticExecutionResult("BLOCKED", (), (step.element_id,), tuple(sorted(pending_ids)))

            action = SimpleNamespace(intent=GuiIntent.CREATE, tool=step.gui_tool)
            result = self.executor.execute(action)
            if not result.success:
                return SemanticExecutionResult(
                    "BLOCKED",
                    (),
                    (step.element_id,),
                    tuple(sorted(pending_ids)),
                )

            remaining = tuple(sorted(pending_ids - {step.element_id}))
            return SemanticExecutionResult(
                "PARTIAL" if remaining else "COMPLETE",
                (step.element_id,),
                (),
                remaining,
            )

        return SemanticExecutionResult("NO_PROGRESS", (), (), tuple(sorted(pending_ids)))

    def execute_until_blocked(
        self,
        desired: WindowModel,
        topology: WindowTopology,
        observed: WindowModel,
    ) -> SemanticExecutionResult:
        changes = diff_models(desired, observed)
        pending_ids = {
            change.element_id
            for change in changes
            if change.change == WindowChangeType.ADD
        }
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

            action = SimpleNamespace(intent=GuiIntent.CREATE, tool=step.gui_tool)
            result = self.executor.execute(action)
            if not result.success:
                blocked.append(step.element_id)
                break
            executed.append(step.element_id)

        remaining = tuple(
            step.element_id
            for step in steps
            if step.element_id in pending_ids and step.element_id not in executed
        )
        status = "BLOCKED" if blocked else ("COMPLETE" if not remaining else "PARTIAL")
        return SemanticExecutionResult(status, tuple(executed), tuple(blocked), remaining)


def single_cell_left_target() -> tuple[WindowModel, WindowTopology]:
    model = WindowModel(properties={"width": 900, "height": 1200, "cells": 1})
    frame = model.add_element("frame", WindowElementType.FRAME)
    cell = model.add_element("cell_left", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    sash = model.add_element("sash_left", WindowElementType.SASH, parent_id=cell.id, opening="left")
    glass = model.add_element("glass_left", WindowElementType.GLASS, parent_id=sash.id, panes=3)
    hardware = model.add_element("hardware_left", WindowElementType.HARDWARE, parent_id=sash.id, system="unknown")

    topology = WindowTopology()
    topology.add(frame, side=WindowSide.CENTER, role="FRAME")
    topology.add(cell, side=WindowSide.LEFT, position_index=0, role="CELL")
    topology.add(sash, side=WindowSide.LEFT, position_index=0, opening="left")
    topology.add(glass, side=WindowSide.LEFT, position_index=0)
    topology.add(hardware, side=WindowSide.LEFT, position_index=0)
    return model, topology
