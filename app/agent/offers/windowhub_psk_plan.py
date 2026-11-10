"""Plan the fields of a two-panel PSK assembly offline."""

from app.wh.model.opening import Opening
from app.wh.runtime.construction_parser import ConstructionParser
from app.window_model.topology import WindowSide


def plan_psk(*, width_mm, height_mm, layout, split_from_left_mm, slide_direction, view):
    """Plan only the explicit fixed-plus-sliding layout inside one frame."""
    if any(type(value) is not int or value <= 0 for value in (width_mm, height_mm)):
        raise ValueError("Podaj dodatnią szerokość i wysokość zestawu PSK w mm.")
    if layout not in ("FIX+PSK", "PSK+FIX"):
        raise ValueError("Podaj kolejność pól PSK od lewej: FIX+PSK albo PSK+FIX.")
    if split_from_left_mm is None:
        raise ValueError("Brakuje wymiaru podziału PSK od lewej krawędzi.")
    if type(split_from_left_mm) is not int or not 0 < split_from_left_mm < width_mm:
        raise ValueError("Wymiar podziału PSK musi leżeć wewnątrz zestawu.")
    if slide_direction not in ("LEFT", "RIGHT"):
        raise ValueError("Brakuje jednoznacznego kierunku przesuwu PSK.")
    if view not in ("inside", "outside"):
        raise ValueError("Podaj widok odniesienia dla stron PSK: od wewnątrz albo od zewnątrz.")

    schema = ConstructionParser().parse(layout)
    fields = [
        {"side": side.value, "role": "sliding" if segment.opening is Opening.PSK else "fixed",
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
        "hardware": {"family": "PSK", "target_side": sliding["side"]},
    }
