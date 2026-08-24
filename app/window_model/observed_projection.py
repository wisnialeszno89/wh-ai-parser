from __future__ import annotations

from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


def _side(value: str | None) -> WindowSide:
    value = (value or "LEFT").upper()
    return {
        "LEFT": WindowSide.LEFT,
        "RIGHT": WindowSide.RIGHT,
        "TOP": WindowSide.TOP,
        "BOTTOM": WindowSide.BOTTOM,
    }.get(value, WindowSide.UNKNOWN)


def project_observed_runtime(gui_state) -> tuple[WindowModel, WindowTopology]:
    model = WindowModel(properties={"source": "runtime"})
    topology = WindowTopology()

    frame_point = gui_state.frame_point or gui_state.last_created_point
    if frame_point is None:
        return model, topology

    frame = model.add_element("frame", WindowElementType.FRAME, point=frame_point)
    topology.add(frame, side=WindowSide.CENTER, role="FRAME")

    side = _side(getattr(gui_state, "panel_side", None))
    side_name = side.value.lower()
    index = 0 if side is WindowSide.LEFT else 1 if side is WindowSide.RIGHT else None

    cell = model.add_element(
        f"cell_{side_name}",
        WindowElementType.MULLION,
        parent_id=frame.id,
        role="CELL",
    )
    topology.add(cell, side=side, position_index=index, role="CELL")

    if gui_state.sash_point is not None:
        sash = model.add_element(
            f"sash_{side_name}",
            WindowElementType.SASH,
            parent_id=cell.id,
            point=gui_state.sash_point,
        )
        topology.add(
            sash,
            side=side,
            position_index=index,
            opening=getattr(gui_state, "opening", None),
        )

        if gui_state.glass_point is not None:
            glass = model.add_element(
                f"glass_{side_name}",
                WindowElementType.GLASS,
                parent_id=sash.id,
                point=gui_state.glass_point,
            )
            topology.add(glass, side=side, position_index=index)

    return model, topology
