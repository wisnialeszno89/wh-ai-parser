from app.runtime.execution.gui_execution_state import GuiExecutionState
from app.window_model.observed_projection import project_observed_runtime


def main() -> None:
    state = GuiExecutionState(
        frame_point=(223, 625),
        sash_point=(223, 642),
        glass_point=(223, 625),
        last_created_point=(223, 625),
        panel_side="right",
    )

    model, topology = project_observed_runtime(state)
    print(f"[OBSERVED MODEL] elements={len(model.elements)}")
    for element in model.elements.values():
        print(
            f"[ELEMENT] id={element.id} type={element.type.value} "
            f"parent={element.parent_id} properties={element.properties}"
        )
    print("[TOPOLOGY]")
    for node in topology.nodes.values():
        print(
            f"[NODE] id={node.element_id} side={node.side.value} "
            f"index={node.position_index} role={node.role} opening={node.opening}"
        )

    errors = model.validate() + topology.validate(model)
    print(f"[VALIDATE] errors={errors}")
    if errors:
        raise SystemExit(1)
    print("[PROBE] COMPLETE. Observed runtime projects into semantic topology.")


if __name__ == "__main__":
    main()
