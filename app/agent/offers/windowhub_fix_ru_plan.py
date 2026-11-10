"""Build a semantic plan for a fixed field and a tilt-and-turn field."""

from pathlib import Path

from app.knowledge.openings.opening_repository import OpeningRepository
from app.wh.model.opening import Opening
from app.wh.runtime.construction_parser import ConstructionParser
from app.window_model.dependency_planner import DependencyPlanner, ExecutableStep
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


def plan_fix_ru(
    *,
    width_mm: int,
    height_mm: int,
    layout: str,
    split_from_left_mm: int | None,
    opening_code: str | None,
) -> list[ExecutableStep]:
    """Plan an explicit vertical split. Dimensions are from the drawing, not cut sizes."""
    if any(type(value) is not int or value <= 0 for value in (width_mm, height_mm)):
        raise ValueError("Podaj dodatnią szerokość i wysokość okna w mm.")
    if layout not in {"FIX+RU", "RU+FIX"}:
        raise ValueError("Podaj kolejność pól od lewej: FIX+RU albo RU+FIX.")
    if split_from_left_mm is None:
        raise ValueError("Brakuje wymiaru podziału od lewej krawędzi.")
    if type(split_from_left_mm) is not int or not 0 < split_from_left_mm < width_mm:
        raise ValueError("Wymiar podziału musi leżeć pomiędzy lewą a prawą krawędzią okna.")
    if opening_code not in {"DKL", "DKR"}:
        raise ValueError("Podaj kierunek skrzydła RU: DKL albo DKR.")
    repository = OpeningRepository()
    repository.DATA_PATH = Path(__file__).resolve().parents[2] / "knowledge/openings/openings.json"
    opening = repository.get_by_code_or_alias(opening_code)
    if opening is None or opening.opening_type != "TILT_TURN" or opening.direction not in {"LEFT", "RIGHT"}:
        raise ValueError(f"Brak jednoznacznej definicji otwierania {opening_code}.")

    model = WindowModel()
    topology = WindowTopology()
    frame = model.add_element("frame", WindowElementType.FRAME, width_mm=width_mm, height_mm=height_mm)
    topology.add(frame, side=WindowSide.CENTER)
    mullion = model.add_element("fixed_vertical_mullion", WindowElementType.MULLION,
                                parent_id=frame.id, offset_from_left_mm=split_from_left_mm)
    topology.add(mullion, side=WindowSide.CENTER)

    schema = ConstructionParser().parse(layout)
    fields = zip(
        (WindowSide.LEFT, WindowSide.RIGHT),
        schema.segments,
        (split_from_left_mm, width_mm - split_from_left_mm),
    )
    for side, segment, field_width in fields:
        name = side.value.lower()
        parent = frame
        if segment.opening == Opening.TILT_TURN:
            parent = model.add_element(f"sash_{name}", WindowElementType.SASH, parent_id=frame.id,
                                       field_width_mm=field_width, opening=segment.opening.value)
            topology.add(parent, side=side)
            hardware = model.add_element(f"hardware_{name}", WindowElementType.HARDWARE,
                                          parent_id=parent.id, opening_code=opening_code,
                                          direction=opening.direction)
            topology.add(hardware, side=side)
        glass = model.add_element(f"glass_{name}", WindowElementType.GLASS, parent_id=parent.id,
                                  field_width_mm=field_width)
        topology.add(glass, side=side)

    return DependencyPlanner().plan(model, topology)
