from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.window_model.model import WindowElement, WindowElementType, WindowModel


class WindowSide(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    CENTER = "CENTER"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TopologyNode:
    element_id: str
    side: WindowSide = WindowSide.UNKNOWN
    position_index: int | None = None
    role: str | None = None
    opening: str | None = None


@dataclass
class WindowTopology:
    """Semantic layout of window cells/elements independent of WindowHub pixels."""

    nodes: dict[str, TopologyNode] = field(default_factory=dict)

    def add(self, element: WindowElement, *, side: WindowSide = WindowSide.UNKNOWN, position_index: int | None = None, role: str | None = None, opening: str | None = None) -> TopologyNode:
        node = TopologyNode(
            element_id=element.id,
            side=side,
            position_index=position_index,
            role=role,
            opening=opening,
        )
        self.nodes[element.id] = node
        return node

    def node(self, element_id: str) -> TopologyNode | None:
        return self.nodes.get(element_id)

    def elements_on_side(self, side: WindowSide) -> list[TopologyNode]:
        return [node for node in self.nodes.values() if node.side == side]

    def children_by_side(self, model: WindowModel, parent_id: str, side: WindowSide) -> list[WindowElement]:
        ids = {node.element_id for node in self.elements_on_side(side)}
        return [element for element in model.children_of(parent_id) if element.id in ids]

    def validate(self, model: WindowModel) -> list[str]:
        errors: list[str] = []
        known = {model.id, *model.elements.keys()}
        for element_id, node in self.nodes.items():
            if element_id not in known:
                errors.append(f"Topology references unknown element: {element_id}")
            if node.position_index is not None and node.position_index < 0:
                errors.append(f"Topology position_index must be >= 0: {element_id}")
        return errors


def infer_topology(model: WindowModel) -> WindowTopology:
    topology = WindowTopology()
    frame = next(iter(model.elements_of_type(WindowElementType.FRAME)), None)
    if frame is None:
        return topology

    topology.add(frame, side=WindowSide.CENTER, role="FRAME")
    cells = [element for element in model.children_of(frame.id) if element.type in {WindowElementType.MULLION, WindowElementType.HORIZONTAL_MULLION, WindowElementType.MOVABLE_MULLION}]
    cells.sort(key=lambda element: element.id)

    for index, cell in enumerate(cells):
        lowered = cell.id.lower()
        if "left" in lowered:
            side = WindowSide.LEFT
        elif "right" in lowered:
            side = WindowSide.RIGHT
        elif "top" in lowered:
            side = WindowSide.TOP
        elif "bottom" in lowered:
            side = WindowSide.BOTTOM
        else:
            side = WindowSide.UNKNOWN
        topology.add(cell, side=side, position_index=index, role=cell.properties.get("role"))

        for child in model.children_of(cell.id):
            opening = child.properties.get("opening")
            child_side = side
            topology.add(child, side=child_side, position_index=index, opening=opening)
            for leaf in model.children_of(child.id):
                topology.add(leaf, side=child_side, position_index=index)

    return topology
