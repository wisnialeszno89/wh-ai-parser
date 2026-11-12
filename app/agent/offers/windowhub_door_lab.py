"""Build and verify a single solid-panel entrance door in the local simulator."""

from app.actions.models.action import Action
from app.simulator.window_scene import WindowScene
from app.simulator.window_simulator import WindowSimulator


def simulate_entrance_door(row):
    width, height = row.get("width_mm"), row.get("height_mm")
    if any(type(value) is not int or value <= 0 for value in (width, height)):
        raise ValueError("Podaj dodatnią szerokość i wysokość drzwi w mm.")
    code = row.get("opening")
    if code not in ("DL", "DR"):
        raise ValueError("Podaj rozwierny kierunek drzwi: DL albo DR.")
    direction = "LEFT" if code == "DL" else "RIGHT"
    swing = row.get("swing")
    if swing not in ("inward", "outward"):
        raise ValueError("Potwierdź, czy drzwi otwierają się do wewnątrz czy na zewnątrz.")
    if row.get("infill") != "solid_panel":
        raise ValueError("Potwierdź pełny panel. Przeszklenie wymaga osobnego planu drzwi.")
    if row.get("glazing_panes") is not None:
        raise ValueError("Wyjaśnij jednoczesny zapis pełnego panelu i pakietu szybowego.")

    simulator = WindowSimulator(WindowScene.empty(width, height))
    stages = (
        ("frame", Action("select_tool", tool_name="frame_tool"), Action("draw_frame")),
        ("door_leaf", Action("select_tool", tool_name="sash_tool"), Action("add_door_leaf")),
        ("solid_panel", Action("select_tool", tool_name="panel_tool"), Action("add_door_panel", value=row["infill"])),
        ("door_hinges", Action("select_tool", tool_name="hardware_tool"),
         Action("add_door_hinges", value=f"{direction}:{swing}")),
    )
    trace = []
    for stage, *actions in stages:
        outcome = simulator.apply(actions)
        if outcome.rejected:
            raise ValueError(f"Symulator odrzucił etap {stage}: {outcome.rejected}")
        trace.append({"stage": stage, "actions": outcome.applied, "scene": simulator.scene.semantic_snapshot()})

    actual = trace[-1]["scene"]
    if (
        actual["opening"] != {"width": width, "height": height}
        or [element["kind"] for element in actual["elements"]] != ["FRAME", "DOOR_LEAF", "SOLID_PANEL", "DOOR_HINGES"]
    ):
        raise ValueError("Odczyt nie potwierdził kompletnej konstrukcji drzwi.")
    frame, leaf, panel, hinges = actual["elements"]
    if (
        leaf["parent_id"] != frame["id"] or panel["parent_id"] != leaf["id"] or hinges["parent_id"] != leaf["id"]
        or leaf.get("opening") != "TURN" or leaf.get("direction") != direction or leaf.get("swing") != swing
    ):
        raise ValueError("Odczyt nie potwierdził wypełnienia, zawiasów lub kierunku otwierania drzwi.")
    return {"direction": leaf["direction"], "swing": leaf["swing"], "trace": trace, "scene": actual}
