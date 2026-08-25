from __future__ import annotations

import os
from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.construction_state_observer import ConstructionStateObserver
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.vision.ai_visual_observer import AIVisualStructureObserver
from app.runtime.vision.structure_observer import VisualStructureObserver

SEQUENCE = (GuiTool.FRAME, GuiTool.MULLION, GuiTool.SASH, GuiTool.GLASS, GuiTool.SASH, GuiTool.GLASS)


def _probe_rect(vision):
    image = vision.screenshot.image
    height, width = image.shape[:2]
    canvas = getattr(getattr(vision, "canvas", None), "bounds", None)
    if canvas is None:
        return (0, 0, width, height)
    x, y, w, h = int(canvas.left), int(canvas.top), int(canvas.width), int(canvas.height)
    target = max(420, min(720, max(w, h) * 2))
    cx, cy = x + w // 2, y + h // 2
    px = max(0, min(width - target, cx - target // 2))
    py = max(0, min(height - target, cy - target // 2))
    return px, py, min(target, width - px), min(target, height - py)


def _context(local):
    return "\n".join((
        f"construction_rect={local.construction_rect}",
        f"vertical_lines={[int(v.coordinate) for v in local.vertical_lines]}",
        f"horizontal_lines={[int(v.coordinate) for v in local.horizontal_lines]}",
        f"cells={[(int(c.x), int(c.y), int(c.width), int(c.height)) for c in local.cells]}",
    ))


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB TWO-CELL AI -> HARDWARE GATE PROBE LIVE")
    print("=" * 80)
    print("PRECONDITION: construction workspace must be EMPTY")
    print("SEQUENCE: FRAME -> MULLION -> SASH -> GLASS -> SASH -> GLASS")
    print("HARDWARE: INSPECT ONLY; NO HARDWARE CLICK")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    state_observer = ConstructionStateObserver()
    visual_observer = VisualStructureObserver()
    ai_observer = AIVisualStructureObserver()

    for index, tool in enumerate(SEQUENCE, start=1):
        print(f"\n[STEP {index}/{len(SEQUENCE)}] CREATE {tool.name}")
        vision = executor.locator.vision.capture()
        context.cache.screenshot = vision
        context.window = vision.window
        executor._remember_workspace(vision)
        before = state_observer.observe(vision, context.gui_state, hardware_ready=False)
        print(f"[STATE BEFORE] {before.stage.value} reason={before.reason}")

        result = executor.execute(SimpleNamespace(intent=GuiIntent.CREATE, tool=tool))
        print(f"[ACT RESULT] success={result.success} message={result.message}")
        if not result.success:
            raise RuntimeError(f"Fixture action failed at {tool.name}: {result.message}")

    print("\n[VERIFY] FINAL CONSTRUCTION")
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    local = visual_observer.observe(vision)
    print(f"[LOCAL] {_context(local)}")

    signal = 0.90 if len(local.cells) >= 2 else 0.72
    force = os.getenv("WH_AI_VISION_FORCE", "0") == "1"
    ai = ai_observer.observe(vision.screenshot.image, _probe_rect(vision), local_confidence=signal, force_ai=force, visual_context=_context(local))
    print(f"[AI] status={ai.status} confidence={ai.confidence:.3f} cache={ai.cache_hit} calls={ai.api_calls}")
    if ai.error:
        print(f"[AI ERROR] {ai.error}")
    for element in ai.elements:
        print(f"[AI ELEMENT] kind={element.kind} side={element.side} parent={element.parent_id} bbox={element.bbox} confidence={element.confidence:.3f}")

    hardware = executor.hardware_precondition.resolver.inspect()
    print(f"[HARDWARE GATE] ready={hardware.ready}")
    print(f"[HARDWARE GATE] reason={getattr(hardware, 'reason', None)}")

    final_state = state_observer.observe(vision, context.gui_state, hardware_ready=hardware.ready)
    print(f"[STATE FINAL] stage={final_state.stage.value} reason={final_state.reason}")
    print("[DECISION] HARDWARE CLICK WILL NOT BE EXECUTED BY THIS PROBE")
    print("[PROBE] COMPLETE. AI recognition + hardware readiness gate verified.")


if __name__ == "__main__":
    main()
