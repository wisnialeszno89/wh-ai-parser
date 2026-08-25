from __future__ import annotations

import os

from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.vision.ai_visual_observer import AIVisualStructureObserver
from app.runtime.vision.structure_observer import VisualStructureObserver


def _probe_rect(vision) -> tuple[int, int, int, int]:
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
    return int(px), int(py), int(min(target, width - px)), int(min(target, height - py))


def _visual_context(local) -> str:
    parts = [
        f"construction_rect={local.construction_rect}",
        f"vertical_lines={[int(v.coordinate) for v in local.vertical_lines]}",
        f"horizontal_lines={[int(v.coordinate) for v in local.horizontal_lines]}",
        f"cells={[(int(c.x), int(c.y), int(c.width), int(c.height)) for c in local.cells]}",
    ]
    return "\n".join(parts)


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB AI VISUAL STRUCTURE OBSERVER LIVE")
    print("=" * 80)
    print("NO GUI CLICKS")
    print("AI network calls are disabled by default.")

    context = ExecutionContext(mouse_enabled=False, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window

    image = vision.screenshot.image
    rect = _probe_rect(vision)
    local = VisualStructureObserver().observe(vision)

    signal = 0.20
    if len(local.cells) >= 2:
        signal = 0.82
    elif len(local.vertical_lines) >= 3 or len(local.horizontal_lines) >= 3:
        signal = 0.72
    elif local.construction_rect is not None:
        signal = 0.58

    force = os.getenv("WH_AI_VISION_FORCE", "0") == "1"
    observer = AIVisualStructureObserver()
    observation = observer.observe(
        image,
        rect,
        local_confidence=signal,
        force_ai=force,
        visual_context=_visual_context(local),
    )

    print(f"[AI ENABLED] {os.getenv('WH_AI_VISION_ENABLED', '0')}")
    print(f"[MODEL] {os.getenv('WH_AI_VISION_MODEL', AIVisualStructureObserver.DEFAULT_MODEL)}")
    print(f"[LOCAL SIGNAL] {signal:.2f}")
    print(f"[FORCE AI] {force}")
    print(f"[LOCAL CONTEXT]\n{_visual_context(local)}")
    print(f"[ANALYSIS RECT] {observation.analysis_rect}")
    print(f"[STATUS] {observation.status}")
    print(f"[CONFIDENCE] {observation.confidence:.3f}")
    print(f"[CACHE HIT] {observation.cache_hit}")
    print(f"[API CALLS] {observation.api_calls}")
    if observation.error:
        print(f"[ERROR] {observation.error}")

    if observation.raw_json:
        print("[AI PAYLOAD]")
        for key, value in observation.raw_json.items():
            print(f"  {key}={value}")

    for element in observation.elements:
        print(
            f"[ELEMENT] id={element.id} kind={element.kind} side={element.side} "
            f"parent={element.parent_id} bbox={element.bbox} confidence={element.confidence:.3f} "
            f"properties={element.properties}"
        )

    print("[PROBE] COMPLETE. Recognition stage is isolated from GUI execution.")


if __name__ == "__main__":
    main()