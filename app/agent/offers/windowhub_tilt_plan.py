"""Plan single-sash openings without choosing a catalog fitting."""

from pathlib import Path

from app.knowledge.openings.opening_repository import OpeningRepository
from app.wh.model.opening import Opening
from app.window_model.dependency_planner import DependencyPlanner, ExecutableStep
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


def plan_single_tilt(*, width_mm: int, height_mm: int) -> list[ExecutableStep]:
    return _plan_single_sash(width_mm, height_mm, Opening.TILT)


def plan_single_tilt_turn(*, width_mm: int, height_mm: int, opening_code: str, glazing_panes: int) -> list[ExecutableStep]:
    if opening_code not in ("DKL", "DKR"):
        raise ValueError("Podaj kierunek skrzydła: DKL albo DKR.")
    if type(glazing_panes) is not int or glazing_panes <= 0:
        raise ValueError("Podaj liczbę szyb w pakiecie.")
    repository = OpeningRepository()
    repository.DATA_PATH = Path(__file__).resolve().parents[2] / "knowledge/openings/openings.json"
    definition = repository.get_by_code_or_alias(opening_code)
    if definition is None or definition.opening_type != "TILT_TURN" or definition.direction not in ("LEFT", "RIGHT"):
        raise ValueError(f"Brak jednoznacznej definicji otwierania {opening_code}.")
    return _plan_single_sash(width_mm, height_mm, Opening.TILT_TURN, glazing_panes, definition.direction)


def _plan_single_sash(width_mm, height_mm, opening, glazing_panes=None, direction=None):
    if any(type(value) is not int or value <= 0 for value in (width_mm, height_mm)):
        raise ValueError("Podaj dodatnią szerokość i wysokość okna w mm.")

    model = WindowModel()
    topology = WindowTopology()
    frame = model.add_element("frame", WindowElementType.FRAME, width_mm=width_mm, height_mm=height_mm)
    sash = model.add_element("sash", WindowElementType.SASH, parent_id=frame.id, opening=opening.value)
    glass_spec = {} if glazing_panes is None else {"panes": glazing_panes}
    glass = model.add_element("glass", WindowElementType.GLASS, parent_id=sash.id, **glass_spec)
    hardware_spec = {} if direction is None else {"direction": direction}
    hardware = model.add_element("hardware", WindowElementType.HARDWARE, parent_id=sash.id,
                                 opening=opening.value, **hardware_spec)
    for element in (frame, sash, glass, hardware):
        topology.add(element, side=WindowSide.CENTER)
    return DependencyPlanner().plan(model, topology)
