"""Plan the fields of a two-panel PSK assembly offline."""

from app.wh.model.opening import Opening
from app.wh.runtime.construction_parser import ConstructionParser
from app.window_model.topology import WindowSide


def plan_psk(**spec):
    return _plan_sliding(Opening.PSK, **spec)


def plan_hst(**spec):
    return _plan_sliding(Opening.HST, **spec)


def _plan_sliding(opening, *, width_mm, height_mm, layout, split_from_left_mm, slide_direction, view):
    """Plan only the explicit fixed-plus-sliding layout inside one frame."""
    family = opening.name
    if any(type(value) is not int or value <= 0 for value in (width_mm, height_mm)):
        raise ValueError(f"Podaj dodatnią szerokość i wysokość zestawu {family} w mm.")
    if layout not in (f"FIX+{family}", f"{family}+FIX"):
        raise ValueError(f"Podaj kolejność pól {family} od lewej: FIX+{family} albo {family}+FIX.")
    if split_from_left_mm is None:
        raise ValueError(f"Brakuje wymiaru podziału {family} od lewej krawędzi.")
    if type(split_from_left_mm) is not int or not 0 < split_from_left_mm < width_mm:
        raise ValueError(f"Wymiar podziału {family} musi leżeć wewnątrz zestawu.")
    if slide_direction not in ("LEFT", "RIGHT"):
        raise ValueError(f"Brakuje jednoznacznego kierunku przesuwu {family}.")
    if view not in ("inside", "outside"):
        raise ValueError(f"Podaj widok odniesienia dla stron {family}: od wewnątrz albo od zewnątrz.")

    schema = ConstructionParser().parse(layout)
    fields = [
        {"side": side.value, "role": "sliding" if segment.opening is opening else "fixed",
         "field_width_mm": width}
        for side, segment, width in zip(
            (WindowSide.LEFT, WindowSide.RIGHT), schema.segments,
            (split_from_left_mm, width_mm - split_from_left_mm),
        )
    ]
    fixed = next(field for field in fields if field["role"] == "fixed")
    sliding = next(field for field in fields if field["role"] == "sliding")
    if slide_direction != fixed["side"]:
        raise ValueError("W tym układzie kierunek przesuwu musi prowadzić w stronę pola stałego.")
    return {
        "width_mm": width_mm, "height_mm": height_mm, "split_from_left_mm": split_from_left_mm,
        "view": view, "fields": fields, "slide_direction": slide_direction,
        "hardware": {"family": family, "target_side": sliding["side"]},
    }
