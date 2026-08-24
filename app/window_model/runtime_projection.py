from __future__ import annotations

from app.runtime.execution.gui_execution_state import GuiExecutionState
from app.window_model.model import WindowElementType, WindowModel


def project_runtime_state(state: GuiExecutionState) -> WindowModel:
    """Project the current GUI runtime memory into the canonical window model.

    This is intentionally a projection, not a visual truth source. It lets
    execution and planning speak the same semantic language while preserving
    the distinction between runtime memory and future vision-based observation.
    """
    model = WindowModel()
    frame = None
    if state.frame_point is not None:
        frame = model.add_element(
            "frame",
            WindowElementType.FRAME,
            parent_id=model.id,
            point=state.frame_point,
        )

    if frame is None:
        return model

    # Current v1 runtime tracks one active sash/glass chain. Keep it semantic
    # rather than pretending to know a full multi-cell topology.
    cell = model.add_element(
        "cell_current",
        WindowElementType.MULLION,
        parent_id=frame.id,
        role="CELL",
    )

    sash = None
    if state.sash_point is not None:
        sash = model.add_element(
            "sash_current",
            WindowElementType.SASH,
            parent_id=cell.id,
            point=state.sash_point,
        )

    if sash is not None and state.glass_point is not None:
        model.add_element(
            "glass_current",
            WindowElementType.GLASS,
            parent_id=sash.id,
            point=state.glass_point,
        )

    return model
