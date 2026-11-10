"""Plan a single-sash tilt-only window without choosing a catalog fitting."""

from app.wh.model.opening import Opening
from app.window_model.dependency_planner import DependencyPlanner, ExecutableStep
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


def plan_single_tilt(*, width_mm: int, height_mm: int) -> list[ExecutableStep]:
    if any(type(value) is not int or value <= 0 for value in (width_mm, height_mm)):
        raise ValueError("Podaj dodatnią szerokość i wysokość okna uchylnego w mm.")

    model = WindowModel()
    topology = WindowTopology()
    frame = model.add_element("frame", WindowElementType.FRAME, width_mm=width_mm, height_mm=height_mm)
    sash = model.add_element("sash", WindowElementType.SASH, parent_id=frame.id, opening=Opening.TILT.value)
    glass = model.add_element("glass", WindowElementType.GLASS, parent_id=sash.id)
    hardware = model.add_element("hardware", WindowElementType.HARDWARE, parent_id=sash.id, opening=Opening.TILT.value)
    for element in (frame, sash, glass, hardware):
        topology.add(element, side=WindowSide.CENTER)
    return DependencyPlanner().plan(model, topology)
