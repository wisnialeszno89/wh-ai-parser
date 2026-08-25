from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.vision.structure_observer import VisualStructureObserver


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB VISUAL STRUCTURE OBSERVER LIVE")
    print("=" * 80)
    print("NO GUI CLICKS")

    context = ExecutionContext(mouse_enabled=False, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window

    observer = VisualStructureObserver()
    structure = observer.observe(vision)

    print(f"[CONSTRUCTION] {structure.construction_rect}")
    print(f"[VERTICAL LINES] {len(structure.vertical_lines)}")
    for line in structure.vertical_lines:
        print(f"[V] x={line.coordinate} strength={line.strength:.4f}")
    print(f"[HORIZONTAL LINES] {len(structure.horizontal_lines)}")
    for line in structure.horizontal_lines:
        print(f"[H] y={line.coordinate} strength={line.strength:.4f}")
    print(f"[CELLS] {len(structure.cells)}")
    for index, cell in enumerate(structure.cells):
        print(
            f"[CELL {index}] rect=({cell.x},{cell.y},{cell.width}x{cell.height}) "
            f"center=({cell.center_x},{cell.center_y})"
        )
    print("[PROBE] COMPLETE. Vision structure was derived from screenshot only.")


if __name__ == "__main__":
    main()
