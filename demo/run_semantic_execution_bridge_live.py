from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.window_model.observed_projection import project_observed_runtime
from app.window_model.semantic_executor import SemanticExecutionBridge, single_cell_left_target


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB SEMANTIC EXECUTION BRIDGE LIVE")
    print("=" * 80)
    print("TARGET: one left cell, sash, glass, hardware")
    print("MODE: OBSERVE -> SEMANTIC DIFF -> DEPENDENCY PLAN -> ACT")
    print("HARDWARE: deliberately blocked by bridge for this milestone")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    bridge = SemanticExecutionBridge(executor)

    desired, topology = single_cell_left_target()
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    executor._remember_workspace(vision)

    observed, _ = project_observed_runtime(context.gui_state)
    print(f"[OBSERVED BEFORE] elements={len(observed.elements)}")

    result = bridge.execute_until_blocked(desired, topology, observed)
    print(f"[SEMANTIC RESULT] status={result.status}")
    print(f"[EXECUTED] {list(result.executed)}")
    print(f"[BLOCKED] {list(result.blocked)}")
    print(f"[REMAINING] {list(result.remaining)}")

    print("[PROBE] COMPLETE. Semantic plan was routed into the existing executor.")


if __name__ == "__main__":
    main()
