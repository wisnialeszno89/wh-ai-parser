from __future__ import annotations

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.construction_state_observer import ConstructionStateObservation, ConstructionStage


class ConstructionPlanner:
    """Choose the next missing construction action from observed state.

    The planner is deliberately deterministic for v1. It does not click and it
    does not assume that runtime history equals WindowHub truth. Its output is
    a proposed next tool for the executor to verify and perform.
    """

    def next_tool(self, observation: ConstructionStateObservation) -> GuiTool | None:
        if observation.stage == ConstructionStage.EMPTY_WORKSPACE:
            return GuiTool.FRAME
        if observation.stage == ConstructionStage.EXTERNAL_CONSTRUCTION:
            return None
        if observation.stage == ConstructionStage.HARDWARE_READY:
            return None
        if not observation.frame_present:
            return GuiTool.FRAME
        if not observation.sash_present:
            return GuiTool.SASH
        if not observation.glass_present:
            return GuiTool.GLASS
        if observation.stage == ConstructionStage.READY_FOR_HARDWARE:
            return GuiTool.HARDWARE
        return None
