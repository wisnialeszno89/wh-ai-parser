from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.gui.enums.gui_tool import GuiTool
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


class TopologyPlanAction(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"


@dataclass(frozen=True)
class TopologyPlanStep:
    action: TopologyPlanAction
    element_id: str
    element_type: WindowElementType
    side: WindowSide
    parent_id: str | None
    gui_tool: GuiTool | None
    details: dict


class TopologyConstructionPlanner:
    """Turn semantic topology gaps into deterministic construction steps."""

    _TOOL_BY_TYPE = {
        WindowElementType.FRAME: GuiTool.FRAME,
        WindowElementType.SASH: GuiTool.SASH,
        WindowElementType.GLASS: GuiTool.GLASS,
        WindowElementType.HARDWARE: GuiTool.HARDWARE,
        WindowElementType.MULLION: GuiTool.MULLION,
        WindowElementType.HORIZONTAL_MULLION: GuiTool.HORIZONTAL_MULLION,
        WindowElementType.MOVABLE_MULLION: GuiTool.MOVABLE_MULLION,
        WindowElementType.CONNECTOR: GuiTool.CONNECTOR,
        WindowElementType.LIMITER: GuiTool.LIMITER,
    }

    def plan(self, desired: WindowModel, observed: WindowModel, desired_topology: WindowTopology, observed_topology: WindowTopology) -> list[TopologyPlanStep]:
        steps: list[TopologyPlanStep] = []

        # Parent/container elements must exist before their descendants.
        desired_ids = set(desired.elements)
        observed_ids = set(observed.elements)
        pending = [desired.elements[element_id] for element_id in desired_ids - observed_ids]

        order = {
            WindowElementType.FRAME: 0,
            WindowElementType.MULLION: 1,
            WindowElementType.HORIZONTAL_MULLION: 1,
            WindowElementType.MOVABLE_MULLION: 1,
            WindowElementType.SASH: 2,
            WindowElementType.GLASS: 3,
            WindowElementType.HARDWARE: 4,
            WindowElementType.CONNECTOR: 5,
            WindowElementType.LIMITER: 6,
        }
        pending.sort(key=lambda item: (order.get(item.type, 99), item.parent_id or "", item.id))

        for element in pending:
            node = desired_topology.node(element.id)
            side = node.side if node else WindowSide.UNKNOWN
            gui_tool = self._TOOL_BY_TYPE.get(element.type)
            steps.append(
                TopologyPlanStep(
                    action=TopologyPlanAction.ADD,
                    element_id=element.id,
                    element_type=element.type,
                    side=side,
                    parent_id=element.parent_id,
                    gui_tool=gui_tool,
                    details={
                        "properties": dict(element.properties),
                        "position_index": node.position_index if node else None,
                        "opening": node.opening if node else None,
                        "role": node.role if node else None,
                    },
                )
            )

        for element_id in sorted(observed_ids - desired_ids):
            element = observed.elements[element_id]
            node = observed_topology.node(element_id)
            steps.append(
                TopologyPlanStep(
                    action=TopologyPlanAction.REMOVE,
                    element_id=element.id,
                    element_type=element.type,
                    side=node.side if node else WindowSide.UNKNOWN,
                    parent_id=element.parent_id,
                    gui_tool=None,
                    details={},
                )
            )

        return steps
