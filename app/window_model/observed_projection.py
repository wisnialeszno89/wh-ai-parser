from __future__ import annotations

from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


def project_observed_runtime(gui_state) -> tuple[WindowModel, WindowTopology]:
    model = WindowModel(properties={"source": "runtime"})
    topology = WindowTopology()

    if gui_state.frame_point is None and gui_state.last_created_point is None:
        return model, topology

    frame_point = gui_state.frame_point or gui_state.last_created_point
    frame = model.add_element("frame", WindowElementType.FRAME, point=frame_point)
    topology.add_node(frame.id, WindowSide.CENTER, role="FRAME")

    side = getattr(gui_state, "panel_side", None) or "left"
    side_enum = WindowSide.from_value(side)
    cell_id = f"cell_{side}"
    cell = model.add_element(cell_id, WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    topology.add_node(cell.id, side_enum, index=0 if side_enum is WindowSide.LEFT else 1, role="CELL")

    if gui_state.sash_point is not None:
        sash_id = f"sash_{side}"
        sash = model.add_element(sash_id, WindowElementType.SASH, parent_id=cell.id, point=gui_state.sash_point)
        topology.add_node(sash.id, side_enum, index=0 if side_enum is WindowSide.LEFT else 1, opening=getattr(gui_state, "opening", None))

        if gui_state.glass_point is not None:
            glass_id = f"glass_{side}"
            glass = model.add_element(glass_id, WindowElementType.GLASS, parent_id=sash.id, point=gui_state.glass_point)
            topology.add_node(glass.id, side_enum, index=0 if side_enum is WindowSide.LEFT else 1)

    return model, topology
