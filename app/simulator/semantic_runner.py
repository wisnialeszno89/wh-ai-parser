from __future__ import annotations

from dataclasses import dataclass

from app.actions.models.action import Action
from app.simulator.window_simulator import SimulationResult, WindowSimulator
from app.window_model.dependency_planner import DependencyPlanner
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowTopology


@dataclass(frozen=True)
class SemanticSimulationResult:
    simulation: SimulationResult
    final_snapshot: dict


class SemanticWindowSimulator:
    """Project the canonical WindowModel execution plan into the deterministic simulator."""

    def __init__(self, simulator: WindowSimulator | None = None) -> None:
        self.simulator = simulator or WindowSimulator()
        self.planner = DependencyPlanner()

    def build_actions(self, desired: WindowModel, topology: WindowTopology) -> list[Action]:
        steps = self.planner.plan(desired, topology)
        actions: list[Action] = []
        mullion_added = False
        hardware_selected = False

        for step in steps:
            if step.element_type is WindowElementType.FRAME:
                actions.extend((Action("select_tool", tool_name="frame_tool"), Action("draw_frame")))
                continue

            if step.element_type in {
                WindowElementType.MULLION,
                WindowElementType.HORIZONTAL_MULLION,
                WindowElementType.MOVABLE_MULLION,
            }:
                # The semantic two-cell model represents cells as MULLION nodes;
                # the simulator needs one physical divider to create those cells.
                if not mullion_added:
                    actions.extend((Action("select_tool", tool_name="mullion_tool"), Action("insert_mullion")))
                    mullion_added = True
                continue

            if step.element_type is WindowElementType.SASH:
                actions.extend(
                    (
                        Action("select_tool", tool_name="sash_tool"),
                        Action("add_sash", value=step.side.value.lower()),
                    )
                )
                continue

            if step.element_type is WindowElementType.GLASS:
                actions.extend(
                    (
                        Action("select_tool", tool_name="glass_tool"),
                        Action("add_glass", value=step.side.value.lower()),
                    )
                )
                continue

            if step.element_type is WindowElementType.HARDWARE:
                if not hardware_selected:
                    system = desired.elements[step.element_id].properties.get("system") or "UR Activpilot"
                    actions.extend(
                        (
                            Action("select_tool", tool_name="hardware_tool"),
                            Action("select_hardware", value=str(system)),
                        )
                    )
                    hardware_selected = True
                actions.append(Action("add_hardware"))
                continue

            raise ValueError(f"Unsupported simulator projection: {step.element_type.value}")

        return actions

    def run(self, desired: WindowModel, topology: WindowTopology) -> SemanticSimulationResult:
        actions = self.build_actions(desired, topology)
        simulation = self.simulator.apply(actions)
        return SemanticSimulationResult(simulation, self.simulator.scene.semantic_snapshot())
