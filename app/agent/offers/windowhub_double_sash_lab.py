"""Build and verify two-sash windows in the local simulator."""

from pathlib import Path

from app.actions.models.action import Action
from app.agent.offers.windowhub_hardware_direction import plan_hardware_inversion
from app.knowledge.openings.opening_repository import OpeningRepository
from app.simulator.window_scene import WindowScene
from app.simulator.window_simulator import SINGLE_SASH_HARDWARE, WindowSimulator


def simulate_double_sash(row, *, auto_direction="RIGHT"):
    if row.get("mullion") != "fixed":
        raise ValueError("Potwierdź słupek stały.")
    return _simulate_two_sashes(row, auto_direction=auto_direction)


def simulate_stulp(row, *, auto_direction="RIGHT"):
    if row.get("mullion") != "movable":
        raise ValueError("Potwierdź słupek ruchomy.")
    active = row.get("active_side")
    if active not in ("left", "right"):
        raise ValueError("Potwierdź, czy chodzi o całe okno, i wskaż lewe albo prawe skrzydło czynne.")
    return _simulate_two_sashes(row, auto_direction=auto_direction, active=active)


def _simulate_two_sashes(row, *, auto_direction, active=None):
    width, height = row.get("width_mm"), row.get("height_mm")
    split = row.get("split_from_left_mm")
    panes = row.get("glazing_panes")
    if any(type(value) is not int or value <= 0 for value in (width, height)):
        raise ValueError("Podaj dodatnią szerokość i wysokość okna w mm.")
    if type(split) is not int or not 0 < split < width:
        raise ValueError("Podaj wymiar podziału od lewej krawędzi.")
    if type(panes) is not int or panes <= 0:
        raise ValueError("Podaj liczbę szyb w pakiecie.")
    if auto_direction not in ("LEFT", "RIGHT"):
        raise ValueError("Brakuje odczytu kierunku nadanego przez okucie.")

    repository = OpeningRepository()
    repository.DATA_PATH = Path(__file__).resolve().parents[2] / "knowledge/openings/openings.json"
    directions = {}
    for side in (active,) if active else ("left", "right"):
        code = row.get(f"{side}_opening")
        if code not in ("DKL", "DKR"):
            raise ValueError(f"Podaj DKL albo DKR dla skrzydła {side}.")
        definition = repository.get_by_code_or_alias(code)
        if definition is None or definition.opening_type != "TILT_TURN":
            raise ValueError(f"Brak definicji otwierania {code}.")
        directions[side] = definition.direction

    simulator = WindowSimulator(WindowScene.empty(width, height), double_sash_auto_direction=auto_direction)
    trace = []

    def apply(stage, *actions):
        result = simulator.apply(actions)
        if result.rejected:
            raise ValueError(f"Symulator odrzucił etap {stage}: {result.rejected}")
        snapshot = simulator.scene.semantic_snapshot()
        trace.append({"stage": stage, "actions": result.applied, "scene": snapshot})
        return {element["id"]: element for element in snapshot["elements"]}

    apply("frame", Action("select_tool", tool_name="frame_tool"), Action("draw_frame"))
    passive = ("right" if active == "left" else "left") if active else None
    if not active:
        apply("fixed_mullion", Action("select_tool", tool_name="mullion_tool"), Action("insert_mullion", value=str(split)))
    apply("sashes", Action("select_tool", tool_name="sash_tool"), Action("add_sash", value="left"),
          Action("add_sash", value="right"))
    if active:
        apply("movable_mullion", Action("select_tool", tool_name="mullion_tool"),
              Action("attach_movable_mullion", target_id=passive, value=str(split)))
    apply("glazing", Action("select_tool", tool_name="glass_tool"), Action("set_glazing_package", value=str(panes)),
          Action("add_glass", value="left"), Action("add_glass", value="right"))
    observed = apply("hardware", Action("select_tool", tool_name="hardware_tool"),
                     Action("select_hardware", value=SINGLE_SASH_HARDWARE),
                     Action("add_stulp_hardware", target_id=active) if active else Action("add_hardware"))
    inversions = {}
    for side, desired in directions.items():
        sash = observed.get(f"sash_{side}", {})
        requested = plan_hardware_inversion(desired, sash.get("direction"), sash.get("inversion_checked"))
        inversions[side] = "unchanged"
        if requested is not None:
            inversions[side] = "on" if requested else "off"
            observed = apply(f"inversion_{side}", Action("set_hardware_inversion", target_id=side,
                                                         value=inversions[side]))

    mullion_id = "stulp_1" if active else "mullion_1"
    expected = {"frame_outer", mullion_id, "sash_left", "sash_right", "glass_left", "glass_right"}
    expected.update(f"hardware_{side}" for side in directions)
    if passive:
        expected.add(f"latch_{passive}")
    final_scene = simulator.scene.semantic_snapshot()
    if (
        set(observed) != expected
        or final_scene["opening"] != {"width": width, "height": height}
        or observed[mullion_id].get("offset_from_left_mm") != split
    ):
        raise ValueError("Odczyt symulatora nie potwierdził ramy, podziału lub liczby elementów.")
    if passive:
        sash = observed[f"sash_{passive}"]
        glass = observed[f"glass_{passive}"]
        mullion = observed[mullion_id]
        latch = observed[f"latch_{passive}"]
        if (
            sash["side"] != passive or sash["parent_id"] != "frame_outer" or sash.get("opening") is not None
            or glass["side"] != passive or glass.get("panes") != panes or glass["parent_id"] != sash["id"]
            or mullion["kind"] != "MOVABLE_MULLION" or mullion["side"] != passive or mullion["parent_id"] != sash["id"]
            or latch["kind"] != "PASSIVE_LATCH" or latch["side"] != passive or latch["parent_id"] != sash["id"]
            or not simulator.hardware_readiness().ready
        ):
            raise ValueError("Odczyt nie potwierdził słupka ruchomego i rygla na skrzydle biernym.")
    for side, desired in directions.items():
        sash, glass, hardware = (observed[f"{kind}_{side}"] for kind in ("sash", "glass", "hardware"))
        if (
            sash["side"] != side or sash["parent_id"] != "frame_outer"
            or sash.get("direction") != desired or sash.get("opening") != "TILT_TURN"
            or glass["side"] != side or glass.get("panes") != panes or glass["parent_id"] != sash["id"]
            or hardware["side"] != side or hardware["parent_id"] != sash["id"]
        ):
            raise ValueError(f"Odczyt nie potwierdził kompletnej konfiguracji skrzydła {side}.")

    result = {"final_directions": {side: observed[f"sash_{side}"]["direction"] for side in directions},
              "inversions": inversions, "trace": trace, "scene": final_scene}
    if active:
        result.update(active_side=active, passive_side=passive)
    return result
