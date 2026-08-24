from app.window_model.model import (
    WindowElementType,
    WindowModel,
    WindowRelationType,
)


def main() -> None:
    model = WindowModel(properties={"width": 1460, "height": 1480})
    frame = model.add_element("frame", WindowElementType.FRAME, parent_id="window")
    left_cell = model.add_element("cell_left", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    right_cell = model.add_element("cell_right", WindowElementType.MULLION, parent_id=frame.id, role="CELL")
    left_sash = model.add_element("sash_left", WindowElementType.SASH, parent_id=left_cell.id, opening="left")
    right_sash = model.add_element("sash_right", WindowElementType.SASH, parent_id=right_cell.id, opening="right")
    model.add_element("glass_left", WindowElementType.GLASS, parent_id=left_sash.id, panes=3)
    model.add_element("glass_right", WindowElementType.GLASS, parent_id=right_sash.id, panes=3)
    model.add_element("hardware_left", WindowElementType.HARDWARE, parent_id=left_sash.id, system="unknown")
    model.add_element("hardware_right", WindowElementType.HARDWARE, parent_id=right_sash.id, system="unknown")
    model.add_relation(frame.id, WindowRelationType.CONTAINS, left_cell.id)
    model.add_relation(frame.id, WindowRelationType.CONTAINS, right_cell.id)

    print("[WINDOW MODEL] elements=", len(model.elements))
    for element in model.elements.values():
        print(
            f"[ELEMENT] id={element.id} type={element.type.value} "
            f"parent={element.parent_id} properties={element.properties}"
        )
    print("[RELATIONS]")
    for relation in model.relations:
        print(
            f"[RELATION] {relation.source_id} "
            f"--{relation.relation.value}--> {relation.target_id}"
        )
    errors = model.validate()
    print(f"[VALIDATE] errors={errors}")
    if errors:
        raise SystemExit(1)
    print("[PROBE] COMPLETE. Canonical window model is valid.")


if __name__ == "__main__":
    main()
