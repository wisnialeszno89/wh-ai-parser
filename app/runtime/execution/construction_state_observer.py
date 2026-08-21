from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConstructionStage(str, Enum):
    EMPTY_WORKSPACE = "empty_workspace"
    EXTERNAL_CONSTRUCTION = "external_construction"
    BUILDING = "building"
    READY_FOR_HARDWARE = "ready_for_hardware"
    HARDWARE_READY = "hardware_ready"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ConstructionStateObservation:
    stage: ConstructionStage
    construction_present: bool
    runtime_history_present: bool
    frame_present: bool
    sash_present: bool
    glass_present: bool
    hardware_ready: bool
    reason: str


class ConstructionStateObserver:
    """Infer a conservative, action-oriented construction state."""

    def observe(self, vision, gui_state, hardware_ready: bool = False) -> ConstructionStateObservation:
        construction_present = getattr(vision, "construction", None) is not None
        frame_present = gui_state.frame_point is not None
        sash_present = gui_state.sash_point is not None
        glass_present = gui_state.glass_point is not None
        runtime_history_present = any(
            value is not None
            for value in (
                gui_state.frame_point,
                gui_state.sash_point,
                gui_state.glass_point,
                gui_state.mullion_point,
                gui_state.last_created_point,
            )
        )

        if hardware_ready:
            stage = ConstructionStage.HARDWARE_READY
            reason = "native HARDWARE command is enabled"
        elif frame_present and sash_present and glass_present:
            stage = ConstructionStage.READY_FOR_HARDWARE
            reason = "runtime state contains FRAME, SASH and GLASS; HARDWARE is not enabled"
        elif runtime_history_present:
            stage = ConstructionStage.BUILDING
            reason = "runtime history contains locally created components; completion is not assumed"
        elif construction_present:
            stage = ConstructionStage.EXTERNAL_CONSTRUCTION
            reason = "construction is visible but runtime has no creation history"
        else:
            stage = ConstructionStage.EMPTY_WORKSPACE
            reason = "no construction is visible and runtime has no creation history"

        return ConstructionStateObservation(
            stage=stage,
            construction_present=construction_present,
            runtime_history_present=runtime_history_present,
            frame_present=frame_present,
            sash_present=sash_present,
            glass_present=glass_present,
            hardware_ready=hardware_ready,
            reason=reason,
        )
