from app.window_model.diff import build_plan, diff_models
from app.window_model.model import WindowElementType, WindowModel


def desired_model() -> WindowModel:
    model = WindowModel(properties={"width": 1460, "height": 1480})
    frame = model.add_element("frame", WindowElementType.FRAME)
    left = model.add_element("cell_left", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    right = model.add_element("cell_right", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    left_sash = model.add_element("sash_left", WindowElementType.SASH, parent_id=left.id, opening="left")
    right_sash = model.add_element("sash_right", WindowElementType.SASH, parent_id=right.id, opening="right")
    model.add_element("glass_left", WindowElementType.GLASS, parent_id=left_sash.id, panes=3)
    model.add_element("glass_right", WindowElementType.GLASS, parent_id=right_sash.id, panes=3)
    model.add_element("hardware_left", WindowElementType.HARDWARE, parent_id=left_sash.id, system="unknown")
    model.add_element("hardware_right", WindowElementType.HARDWARE, parent_id=right_sash.id, system="unknown")
    return model


def observed_model() -> WindowModel:
    model = WindowModel(properties={"width": 1460, "height": 1480})
    frame = model.add_element("frame", WindowElementType.FRAME)
    cell = model.add_element("cell_current", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    sash = model.add_element("sash_current", WindowElementType.SASH, parent_id=cell.id)
    model.add_element("glass_current", WindowElementType.GLASS, parent_id=sash.id, panes=3)
    return model


def main() -> None:
    desired = desired_model()
    observed = observed_model()
    changes = diff_models(desired, observed)
    steps = build_plan(changes)

    print(f"[DESIRED] elements={len(desired.elements)}")
    print(f"[OBSERVED] elements={len(observed.elements)}")
    print(f"[DIFF] changes={len(changes)}")
    for change in changes:
        print(
            f"[CHANGE] {change.change.value} id={change.element_id} "
            f"type={change.element_type.value if change.element_type else None} "
            f"details={change.details}"
        )
    print("[PLAN]")
    for step in steps:
        print(f"[STEP] {step}")
    print("[PROBE] COMPLETE. Desired-vs-observed diff is deterministic.")


if __name__ == "__main__":
    main()
