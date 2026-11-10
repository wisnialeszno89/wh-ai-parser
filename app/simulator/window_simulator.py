from __future__ import annotations

from dataclasses import dataclass, replace

from app.actions.models.action import Action
from app.simulator.hardware import HardwareReadiness, HardwareSpec, HardwareState
from app.simulator.window_scene import SceneElement, WindowScene

SINGLE_SASH_HARDWARE = "UR Activpilot"


@dataclass(frozen=True)
class SimulationResult:
    applied: tuple[str, ...]
    rejected: tuple[str, ...]


class WindowSimulator:
    """Execute the small, safe subset of construction actions used by v1."""

    def __init__(self, scene: WindowScene | None = None, *, single_sash_auto_direction: str | None = None,
                 double_sash_auto_direction: str | None = None) -> None:
        self.scene = scene or WindowScene.empty()
        self.selected_tool: str | None = None
        self.hardware = HardwareState()
        self.single_sash_auto_direction = single_sash_auto_direction
        self.double_sash_auto_direction = double_sash_auto_direction
        self.glazing_panes: int | None = None

    def apply(self, actions: list[Action] | tuple[Action, ...]) -> SimulationResult:
        applied: list[str] = []
        rejected: list[str] = []
        for action in actions:
            try:
                self._apply_one(action)
            except ValueError as exc:
                rejected.append(f"{action.action_type}: {exc}")
            else:
                applied.append(action.action_type)
        return SimulationResult(tuple(applied), tuple(rejected))

    def hardware_readiness(self) -> HardwareReadiness:
        return HardwareReadiness.evaluate(
            has_frame=self.scene.has("FRAME"),
            sash_sides={item.side for item in self.scene.elements if item.kind == "SASH" and item.side},
            glass_sides={item.side for item in self.scene.elements if item.kind == "GLASS" and item.side},
            hardware=self.hardware,
        )

    def _apply_one(self, action: Action) -> None:
        if action.action_type == "select_tool":
            if not action.tool_name:
                raise ValueError("tool_name is required")
            self.selected_tool = action.tool_name
            return

        if action.action_type == "draw_frame":
            self._require_tool("frame_tool")
            if self.scene.has("FRAME"):
                raise ValueError("FRAME already exists")
            self.scene.add(SceneElement("frame_outer", "FRAME"))
            return

        if action.action_type == "insert_mullion":
            self._require_tool("mullion_tool")
            if not self.scene.has("FRAME"):
                raise ValueError("FRAME is required")
            if self.scene.has("MULLION"):
                raise ValueError("MULLION already exists")
            offset = int(action.value) if action.value is not None else None
            if offset is not None and not 0 < offset < self.scene.width:
                raise ValueError("mullion offset must lie inside the frame")
            self.scene.add(SceneElement("mullion_1", "MULLION", "frame_outer", "center", offset_from_left_mm=offset))
            return

        if action.action_type == "attach_movable_mullion":
            self._require_tool("mullion_tool")
            side = action.target_id
            offset = int(action.value or "0")
            if side not in {"left", "right"} or not all(self.scene.has("SASH", side=s) for s in ("left", "right")):
                raise ValueError("two sashes and an explicit passive sash are required")
            if self.scene.has("MULLION") or self.hardware.installed_sides or not 0 < offset < self.scene.width:
                raise ValueError("movable mullion requires a valid split and no fixed mullion")
            self.scene.add(SceneElement("stulp_1", "MOVABLE_MULLION", f"sash_{side}", side,
                                        offset_from_left_mm=offset))
            return

        if action.action_type == "add_sash":
            self._require_tool("sash_tool")
            if not self.scene.has("FRAME"):
                raise ValueError("FRAME is required")
            side = action.value or "left"
            if side == "center":
                if self.scene.has("MULLION") or self.scene.has("SASH"):
                    raise ValueError("a single sash requires an undivided empty frame")
                self.scene.add(SceneElement("sash_center", "SASH", "frame_outer", side))
                return
            if side not in {"left", "right"}:
                raise ValueError("sash side must be left or right")
            element_id = f"sash_{side}"
            if any(item.id == element_id for item in self.scene.elements):
                raise ValueError(f"SASH {side} already exists")
            self.scene.add(SceneElement(element_id, "SASH", "frame_outer", side))
            return

        if action.action_type == "set_glazing_package":
            self._require_tool("glass_tool")
            panes = int(action.value or "0")
            if panes <= 0:
                raise ValueError("glazing must contain at least one pane")
            self.glazing_panes = panes
            return

        if action.action_type == "add_glass":
            self._require_tool("glass_tool")
            side = action.value or "left"
            sash_id = f"sash_{side}"
            if not any(item.id == sash_id for item in self.scene.elements):
                raise ValueError(f"SASH {side} is required")
            glass_id = f"glass_{side}"
            if any(item.id == glass_id for item in self.scene.elements):
                raise ValueError(f"GLASS {side} already exists")
            self.scene.add(SceneElement(glass_id, "GLASS", sash_id, side, panes=self.glazing_panes))
            return

        if action.action_type == "select_hardware":
            self._require_tool("hardware_tool")
            product = (action.value or "").strip()
            if not product:
                raise ValueError("hardware product is required")
            if self.scene.has("SASH", side="center"):
                if product != SINGLE_SASH_HARDWARE:
                    raise ValueError("the single-sash pilot requires ActivPilot")
                self._set_sash_inversion("center", False, self.single_sash_auto_direction)
            self.hardware.selected = HardwareSpec(product=product)
            return

        if action.action_type == "set_hardware_inversion":
            self._require_tool("hardware_tool")
            if self.hardware.selected is None or self.hardware.selected.product != SINGLE_SASH_HARDWARE:
                raise ValueError("ActivPilot must be selected")
            side = action.target_id or "center"
            direction = self.single_sash_auto_direction if side == "center" else self.double_sash_auto_direction
            if side != "center" and side not in self.hardware.installed_sides:
                raise ValueError("hardware must be installed on the target sash")
            if action.value not in {"on", "off"} or direction not in {"LEFT", "RIGHT"}:
                raise ValueError("known inversion state and automatic direction are required")
            self._set_sash_inversion(side, action.value == "on", direction)
            return

        if action.action_type == "add_stulp_hardware":
            self._require_tool("hardware_tool")
            active = action.target_id
            if active not in {"left", "right"}:
                raise ValueError("active sash must be explicit")
            passive = "right" if active == "left" else "left"
            if not self.scene.has("MOVABLE_MULLION", side=passive):
                raise ValueError("movable mullion must belong to the passive sash")
            if not all(self.scene.has("GLASS", side=side) for side in ("left", "right")):
                raise ValueError("both sashes require glazing")
            if self.hardware.selected is None or self.hardware.selected.product != SINGLE_SASH_HARDWARE:
                raise ValueError("ActivPilot must be selected for the active sash in this test")
            if self.hardware.installed_sides or self.double_sash_auto_direction not in {"LEFT", "RIGHT"}:
                raise ValueError("Stulp hardware requires a new installation with a known direction")
            self.scene.add(SceneElement(f"hardware_{active}", "HARDWARE", f"sash_{active}", active))
            self.scene.add(SceneElement(f"latch_{passive}", "PASSIVE_LATCH", f"sash_{passive}", passive))
            self.hardware.selected = HardwareSpec(product=SINGLE_SASH_HARDWARE, required_sides=(active,))
            self.hardware.installed_sides.add(active)
            self._set_sash_inversion(active, False, self.double_sash_auto_direction)
            return

        if action.action_type == "add_hardware":
            self._require_tool("hardware_tool")
            if self.scene.has("MOVABLE_MULLION"):
                raise ValueError("use Stulp hardware for an assembly with a movable mullion")
            if self.hardware.selected is None:
                raise ValueError("hardware product must be selected")
            readiness = self.hardware_readiness()
            if not readiness.ready and "hardware is installed" not in readiness.reason:
                structural_reason = readiness.reason
                if not structural_reason.startswith("hardware sides missing"):
                    raise ValueError(structural_reason)
            for side in self.hardware.selected.required_sides:
                if not self.scene.has("SASH", side=side):
                    raise ValueError(f"SASH {side} is required")
                self.hardware.installed_sides.add(side)
                hardware_id = f"hardware_{side}"
                if not any(item.id == hardware_id for item in self.scene.elements):
                    self.scene.add(SceneElement(hardware_id, "HARDWARE", f"sash_{side}", side))
                    if self.hardware.selected.product == SINGLE_SASH_HARDWARE and self.double_sash_auto_direction:
                        self._set_sash_inversion(side, False, self.double_sash_auto_direction)
            return

        raise ValueError(f"unsupported action: {action.action_type}")

    def _set_sash_inversion(self, side: str, checked: bool, direction: str | None) -> None:
        if checked:
            direction = {"LEFT": "RIGHT", "RIGHT": "LEFT"}[direction]
        for index, item in enumerate(self.scene.elements):
            if item.id == f"sash_{side}":
                self.scene.elements[index] = replace(
                    item, opening="TILT_TURN", direction=direction, inversion_checked=checked,
                )
                return
        raise ValueError(f"SASH {side} is required")

    def _require_tool(self, expected: str) -> None:
        if self.selected_tool != expected:
            raise ValueError(f"tool {expected} must be selected (selected={self.selected_tool!r})")
