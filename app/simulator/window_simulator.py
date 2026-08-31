from __future__ import annotations

from dataclasses import dataclass

from app.actions.models.action import Action
from app.simulator.hardware import HardwareReadiness, HardwareSpec, HardwareState
from app.simulator.window_scene import SceneElement, WindowScene


@dataclass(frozen=True)
class SimulationResult:
    applied: tuple[str, ...]
    rejected: tuple[str, ...]


class WindowSimulator:
    """Execute the small, safe subset of construction actions used by v1."""

    def __init__(self, scene: WindowScene | None = None) -> None:
        self.scene = scene or WindowScene.empty()
        self.selected_tool: str | None = None
        self.hardware = HardwareState()

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
            self.scene.add(SceneElement("mullion_1", "MULLION", "frame_outer", "center"))
            return

        if action.action_type == "add_sash":
            self._require_tool("sash_tool")
            if not self.scene.has("FRAME"):
                raise ValueError("FRAME is required")
            side = action.value or "left"
            if side not in {"left", "right"}:
                raise ValueError("sash side must be left or right")
            element_id = f"sash_{side}"
            if any(item.id == element_id for item in self.scene.elements):
                raise ValueError(f"SASH {side} already exists")
            self.scene.add(SceneElement(element_id, "SASH", "frame_outer", side))
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
            self.scene.add(SceneElement(glass_id, "GLASS", sash_id, side))
            return

        if action.action_type == "select_hardware":
            self._require_tool("hardware_tool")
            product = (action.value or "").strip()
            if not product:
                raise ValueError("hardware product is required")
            self.hardware.selected = HardwareSpec(product=product)
            return

        if action.action_type == "add_hardware":
            self._require_tool("hardware_tool")
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
            return

        raise ValueError(f"unsupported action: {action.action_type}")

    def _require_tool(self, expected: str) -> None:
        if self.selected_tool != expected:
            raise ValueError(f"tool {expected} must be selected (selected={self.selected_tool!r})")
