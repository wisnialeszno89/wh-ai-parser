from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.gui_execution_state import GuiExecutionState
from app.window_model.model import WindowElementType
from app.window_model.runtime_projection import project_runtime_state


def main() -> None:
    state = GuiExecutionState(
        frame_point=(223, 625),
        sash_point=(223, 642),
        glass_point=(223, 625),
        last_created_point=(223, 625),
    )
    context = ExecutionContext(mouse_enabled=False, execution_mode=ExecutionMode.LIVE)
    context.gui_state = state

    model = project_runtime_state(context.gui_state)
    print(f"[RUNTIME PROJECTION] elements={len(model.elements)}")
    for element in model.elements.values():
        print(
            f"[ELEMENT] id={element.id} type={element.type.value} "
            f"parent={element.parent_id} properties={element.properties}"
        )
    print(f"[HAS FRAME] {model.has_type(WindowElementType.FRAME)}")
    print(f"[HAS SASH] {model.has_type(WindowElementType.SASH)}")
    print(f"[HAS GLASS] {model.has_type(WindowElementType.GLASS)}")
    errors = model.validate()
    print(f"[VALIDATE] errors={errors}")
    if errors:
        raise SystemExit(1)
    print("[PROBE] COMPLETE. Runtime state projects into canonical WindowModel.")


if __name__ == "__main__":
    main()
