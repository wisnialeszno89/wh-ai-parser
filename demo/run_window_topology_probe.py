from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, infer_topology


def main() -> None:
    model = WindowModel(properties={"width": 1460, "height": 1480})
    frame = model.add_element("frame", WindowElementType.FRAME, parent_id="window")
    left = model.add_element("cell_left", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    right = model.add_element("cell_right", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    left_sash = model.add_element("sash_left", WindowElementType.SASH, parent_id=left.id, opening="left")
    right_sash = model.add_element("sash_right", WindowElementType.SASH, parent_id=right.id, opening="right")
    model.add_element("glass_left", WindowElementType.GLASS, parent_id=left_sash.id, panes=3)
    model.add_element("glass_right", WindowElementType.GLASS, parent_id=right_sash.id, panes=3)
    model.add_element("hardware_left", WindowElementType.HARDWARE, parent_id=left_sash.id, system="unknown")
    model.add_element("hardware_right", WindowElementType.HARDWARE, parent_id=right_sash.id, system="unknown")

    topology = infer_topology(model)
    errors = topology.validate(model)

    print(f"[TOPOLOGY] nodes={len(topology.nodes)}")
    for node in topology.nodes.values():
        print(
            f"[NODE] id={node.element_id} side={node.side.value} "
            f"index={node.position_index} role={node.role} opening={node.opening}"
        )

    for side in (WindowSide.LEFT, WindowSide.RIGHT, WindowSide.TOP, WindowSide.BOTTOM):
        ids = [node.element_id for node in topology.elements_on_side(side)]
        print(f"[SIDE {side.value}] {ids}")

    print(f"[VALIDATE] errors={errors}")
    if errors:
        raise SystemExit(1)
    print("[PROBE] COMPLETE. Window topology is deterministic and valid.")


if __name__ == "__main__":
    main()
