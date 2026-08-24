from app.gui.enums.gui_tool import GuiTool
from app.window_model.dependency_planner import DependencyPlanner
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, infer_topology


def main():
    model = WindowModel(properties={"width": 1460, "height": 1480})
    frame = model.add_element("frame", WindowElementType.FRAME)
    left = model.add_element("cell_left", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    right = model.add_element("cell_right", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    sash_left = model.add_element("sash_left", WindowElementType.SASH, parent_id=left.id, opening="left")
    sash_right = model.add_element("sash_right", WindowElementType.SASH, parent_id=right.id, opening="right")
    model.add_element("glass_left", WindowElementType.GLASS, parent_id=sash_left.id, panes=3)
    model.add_element("glass_right", WindowElementType.GLASS, parent_id=sash_right.id, panes=3)
    model.add_element("hardware_left", WindowElementType.HARDWARE, parent_id=sash_left.id, system="unknown")
    model.add_element("hardware_right", WindowElementType.HARDWARE, parent_id=sash_right.id, system="unknown")

    topology = infer_topology(model)
    plan = DependencyPlanner().plan(model, topology)

    print(f"[DEPENDENCY PLAN] steps={len(plan)}")
    for i, step in enumerate(plan, 1):
        print(
            f"[STEP {i:02d}] id={step.element_id} type={step.element_type.value} "
            f"side={step.side.value} parent={step.parent_id} gui_tool={step.gui_tool.value}"
        )

    ids = [step.element_id for step in plan]
    assert ids.index("frame") < ids.index("cell_left") < ids.index("sash_left") < ids.index("glass_left") < ids.index("hardware_left")
    assert ids.index("frame") < ids.index("cell_right") < ids.index("sash_right") < ids.index("glass_right") < ids.index("hardware_right")
    assert all(step.gui_tool in GuiTool for step in plan)
    assert not any(step.blocked_by for step in plan)
    print("[VALIDATE] dependency order is executable and acyclic")
    print("[PROBE] COMPLETE. No WindowHub action was sent.")


if __name__ == "__main__":
    main()
