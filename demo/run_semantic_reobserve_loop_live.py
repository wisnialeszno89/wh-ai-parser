from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.window_model.semantic_executor import SemanticExecutionBridge, single_cell_left_target
from app.window_model.observed_projection import project_observed_runtime


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB SEMANTIC RE-OBSERVE LOOP LIVE")
    print("=" * 80)
    print("PRECONDITION: workspace EMPTY")
    print("MODE: OBSERVE -> DIFF -> PLAN -> ACT -> VERIFY -> OBSERVE")
    print("HARDWARE: safe stop when unavailable")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    bridge = SemanticExecutionBridge(executor)
    desired, topology = single_cell_left_target()

    executed: list[str] = []
    blocked: list[str] = []

    for iteration in range(1, 8):
        print(f"\n[ITERATION {iteration}] OBSERVE")
        vision = executor.locator.vision.capture()
        context.cache.screenshot = vision
        context.window = vision.window
        executor._remember_workspace(vision)

        observed, observed_topology = project_observed_runtime(context.gui_state)
        print(f"[OBSERVED] elements={len(observed.elements)} topology_nodes={len(observed_topology.nodes)}")
        print(f"[OBSERVED IDS] {tuple(observed.elements.keys())}")

        pending = [
            e.id for e in desired.elements.values()
            if e.id != desired.id and e.id not in observed.elements
        ]
        print(f"[PENDING] {pending}")
        if not pending:
            print("[RESULT] COMPLETE")
            break

        result = bridge.execute_next(desired, topology, observed)
        print(f"[BRIDGE RESULT] status={result.status}")
        print(f"[BRIDGE EXECUTED] {result.executed}")
        print(f"[BRIDGE BLOCKED] {result.blocked}")
        print(f"[BRIDGE REMAINING] {result.remaining}")

        for item in result.executed:
            if item not in executed:
                executed.append(item)
        for item in result.blocked:
            if item not in blocked:
                blocked.append(item)

        if result.blocked:
            break
        if not result.executed:
            print("[RESULT] NO_PROGRESS")
            break

        executor._refresh_runtime_observation()

    print("\n[FINAL]")
    print(f"executed={executed}")
    print(f"blocked={blocked}")
    print("[PROBE] COMPLETE. Semantic loop re-observed state between every execution step.")


if __name__ == "__main__":
    main()
