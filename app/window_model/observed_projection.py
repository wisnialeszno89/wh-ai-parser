from __future__ import annotations

from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


def _side(value: str | None) -> WindowSide:
    value = (value or "UNKNOWN").upper()
    return {
        "LEFT": WindowSide.LEFT,
        "RIGHT": WindowSide.RIGHT,
        "TOP": WindowSide.TOP,
        "BOTTOM": WindowSide.BOTTOM,
        "CENTER": WindowSide.CENTER,
    }.get(value, WindowSide.UNKNOWN)


def _index(side: WindowSide) -> int | None:
    return {
        WindowSide.LEFT: 0,
        WindowSide.RIGHT: 1,
        WindowSide.TOP: 0,
        WindowSide.BOTTOM: 1,
    }.get(side)


def project_observed_runtime(gui_state) -> tuple[WindowModel, WindowTopology]:
    """Project only semantically verified runtime creations.

    ``panel_side`` describes the NEXT placement target and must never be used
    as evidence that a cell/component already exists.
    """
    model = WindowModel(properties={"source": "runtime"})
    topology = WindowTopology()

    created = getattr(gui_state, "created_element_points", {})
    sides = getattr(gui_state, "created_element_sides", {})
    frame_point = created.get("frame") or gui_state.frame_point or gui_state.last_created_point
    if frame_point is None:
        return model, topology

    frame = model.add_element("frame", WindowElementType.FRAME, point=frame_point)
    topology.add(frame, side=WindowSide.CENTER, role="FRAME")

    ordered_ids = sorted(
        created.keys(),
        key=lambda element_id: (
            10 if element_id.startswith("cell_") else
            20 if element_id.startswith("sash_") else
            30 if element_id.startswith("glass_") else
            40 if element_id.startswith("hardware_") else
            100,
            element_id,
        ),
    )

    for element_id in ordered_ids:
        if element_id == "frame":
            continue
        side = _side(sides.get(element_id))
        position_index = _index(side)
        point = created.get(element_id)
        if element_id.startswith("cell_"):
            element = model.add_element(
                element_id,
                WindowElementType.MULLION,
                parent_id="frame",
                role="CELL",
                point=point,
            )
            topology.add(element, side=side, position_index=position_index, role="CELL")
        elif element_id.startswith("sash_"):
            side_name = element_id.removeprefix("sash_")
            parent_id = f"cell_{side_name}"
            if parent_id not in model.elements:
                continue
            element = model.add_element(
                element_id,
                WindowElementType.SASH,
                parent_id=parent_id,
                point=point,
            )
            topology.add(element, side=side, position_index=position_index)
        elif element_id.startswith("glass_"):
            side_name = element_id.removeprefix("glass_")
            parent_id = f"sash_{side_name}"
            if parent_id not in model.elements:
                continue
            element = model.add_element(
                element_id,
                WindowElementType.GLASS,
                parent_id=parent_id,
                point=point,
            )
            topology.add(element, side=side, position_index=position_index)
        elif element_id.startswith("hardware_"):
            side_name = element_id.removeprefix("hardware_")
            parent_id = f"sash_{side_name}"
            if parent_id not in model.elements:
                continue
            element = model.add_element(
                element_id,
                WindowElementType.HARDWARE,
                parent_id=parent_id,
                point=point,
            )
            topology.add(element, side=side, position_index=position_index)

    return model, topology
