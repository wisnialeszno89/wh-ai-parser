"""Build a single tilt-turn balcony sash with an explicit simulated threshold."""

from app.actions.models.action import Action
from app.agent.offers.windowhub_hardware_direction import plan_hardware_inversion
from app.simulator.window_scene import WindowScene
from app.simulator.window_simulator import SINGLE_SASH_HARDWARE, WindowSimulator


def simulate_balcony_window(row):
    threshold = row.get("threshold")
    if threshold not in ("standard", "low"):
        raise ValueError("Potwierdź typ progu balkonowego: standardowy albo niski.")
    if row.get("single_sash_confirmed") is not True or row.get("swing") != "inward":
        raise ValueError("Potwierdź jedno skrzydło balkonowe otwierane do wewnątrz.")
    width, height = row.get("width_mm"), row.get("height_mm")
    if any(type(value) is not int or value <= 0 for value in (width, height)):
        raise ValueError("Podaj dodatnią szerokość i wysokość w mm.")
    code = row.get("opening")
    if code not in ("DKL", "DKR"):
        raise ValueError("Podaj kierunek skrzydła balkonowego: DKL albo DKR.")
    direction = "LEFT" if code == "DKL" else "RIGHT"
    panes = row.get("glazing_panes")
    if type(panes) is not int or panes <= 0:
        raise ValueError("Podaj liczbę szyb w pakiecie.")

    simulator = WindowSimulator(WindowScene.empty(width, height), single_sash_auto_direction="LEFT")
    trace = []

    def apply(stage, *actions):
        outcome = simulator.apply(actions)
        if outcome.rejected:
            raise ValueError(f"Symulator odrzucił etap {stage}: {outcome.rejected}")
        snapshot = simulator.scene.semantic_snapshot()
        trace.append({"stage": stage, "actions": outcome.applied, "scene": snapshot})
        return snapshot

    apply("frame", Action("select_tool", tool_name="frame_tool"), Action("draw_frame"))
    apply("threshold", Action("select_tool", tool_name="threshold_tool"),
          Action("add_balcony_threshold", value=threshold))
    apply("sash", Action("select_tool", tool_name="sash_tool"), Action("add_sash", value="center"))
    apply("glazing", Action("select_tool", tool_name="glass_tool"),
          Action("set_glazing_package", value=str(panes)), Action("add_glass", value="center"))
    actual = apply("hardware", Action("select_tool", tool_name="hardware_tool"),
                   Action("select_hardware", value=SINGLE_SASH_HARDWARE))
    before = next((item for item in actual["elements"] if item["id"] == "sash_center"), {})
    inversion = plan_hardware_inversion(direction, before.get("direction"), before.get("inversion_checked"))
    if inversion is not None:
        actual = apply("inversion", Action("set_hardware_inversion", value="on" if inversion else "off"))

    elements = actual["elements"]
    if (
        actual["opening"] != {"width": width, "height": height}
        or [item["kind"] for item in elements] != ["FRAME", "THRESHOLD", "SASH", "GLASS"]
    ):
        raise ValueError("Odczyt nie potwierdził kompletnej konstrukcji balkonowej.")
    frame, sill, sash, glass = elements
    if (
        sill["parent_id"] != frame["id"] or sill.get("threshold") != threshold
        or sash["parent_id"] != frame["id"] or sash["side"] != "center"
        or sash.get("opening") != "TILT_TURN" or sash.get("direction") != direction
        or glass["parent_id"] != sash["id"] or glass.get("panes") != panes
        or (inversion is not None and sash.get("inversion_checked") is not inversion)
    ):
        raise ValueError("Odczyt nie potwierdził progu, pakietu szybowego lub otwierania skrzydła.")
    return {"direction": sash["direction"], "panes": glass["panes"], "threshold": sill["threshold"],
            "trace": trace, "scene": actual}
