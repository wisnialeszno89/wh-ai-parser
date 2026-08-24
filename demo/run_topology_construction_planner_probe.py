from app.gui.enums.gui_tool import GuiTool
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology
from app.window_model.topology_planner import TopologyConstructionPlanner


def make_desired() -> tuple[WindowModel, WindowTopology]:
    model = WindowModel(properties={"width": 1460, "height": 1480})
    frame = model.add_element("frame", WindowElementType.FRAME)
    left = model.add_element("cell_left", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    right = model.add_element("cell_right", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    sash_l = model.add_element("sash_left", WindowElementType.SASH, parent_id=left.id, opening="left")
    sash_r = model.add_element("sash_right", WindowElementType.SASH, parent_id=right.id, opening="right")
    model.add_element("glass_left", WindowElementType.GLASS, parent_id=sash_l.id, panes=3)
    model.add_element("glass_right", WindowElementType.GLASS, parent_id=sash_r.id, panes=3)
    model.add_element("hardware_left", WindowElementType.HARDWARE, parent_id=sash_l.id, system="unknown")
    model.add_element("hardware_right", WindowElementType.HARDWARE, parent_id=sash_r.id, system="unknown")

    topology = WindowTopology()
    topology.add(frame, side=WindowSide.CENTER, role="FRAME")
    for element, side, index in (
        (left, WindowSide.LEFT, 0),
        (right, WindowSide.RIGHT, 1),
    ):
        topology.add(element, side=side, position_index=index, role="CELL")
    for element, side, index, opening in (
        (sash_l, WindowSide.LEFT, 0, "left"),
        (sash_r, WindowSide.RIGHT, 1, "right"),
    ):
        topology.add(element, side=side, position_index=index, opening=opening)
    for element, side, index in (
        (model.elements["glass_left"], WindowSide.LEFT, 0),
        (model.elements["hardware_left"], WindowSide.LEFT, 0),
        (model.elements["glass_right"], WindowSide.RIGHT, 1),
        (model.elements["hardware_right"], WindowSide.RIGHT, 1),
    ):
        topology.add(element, side=side, position_index=index)
    return model, topology


def make_observed() -> tuple[WindowModel, WindowTopology]:
    model = WindowModel(properties={"source": "runtime"})
    frame = model.add_element("frame", WindowElementType.FRAME)
    cell = model.add_element("cell_left", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    sash = model.add_element("sash_left", WindowElementType.SASH, parent_id=cell.id, opening="left")
    model.add_element("glass_left", WindowElementType.GLASS, parent_id=sash.id)
    topology = WindowTopology()
    topology.add(frame, side=WindowSide.CENTER, role="FRAME")
    topology.add(cell, side=WindowSide.LEFT, position_index=0, role="CELL")
    topology.add(sash, side=WindowSide.LEFT, position_index=0, opening="left")
    topology.add(model.elements["glass_left"], side=WindowSide.LEFT, position_index=0)
    return model, topology


def main() -> None:
    desired, desired_topology = make_desired()
    observed, observed_topology = make_observed()
    steps = TopologyConstructionPlanner().plan(desired, observed, desired_topology, observed_topology)

    print(f"[TOPOLOGY PLAN] steps={len(steps)}")
    for step in steps:
        print(
            f"[STEP] {step.action.value} id={step.element_id} "
            f"type={step.element_type.value} side={step.side.value} "
            f"parent={step.parent_id} gui_tool={step.gui_tool.name if isinstance(step.gui_tool, GuiTool) else None} "
            f"details={step.details}"
        )

    assert [step.element_id for step in steps[:4]] == ["cell_right", "sash_right", "glass_right", "hardware_left"], (
        "Planner should prioritize missing right-side structure and remaining hardware"
    )
    print("[VALIDATE] topology-aware plan is deterministic")
    print("[PROBE] COMPLETE. No WindowHub action was sent.")


if __name__ == "__main__":
    main()
