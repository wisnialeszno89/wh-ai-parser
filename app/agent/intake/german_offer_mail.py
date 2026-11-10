"""Read a draft from a German enquiry with explicitly named position lines."""

import re

_PIECES = r"(?<![\w.,+-])(\d+)\s*(?:Stk\.?|Stück)(?!\w)"
_POSITION = re.compile(rf"^(?:{_PIECES}\s+)?(Haustür|Haustuer|Fenster)\b\s*:?\s*(.*)$", re.IGNORECASE)
_QUANTITY = re.compile(_PIECES, re.IGNORECASE)
_LAYOUT = re.compile(r"\b[A-Z][A-Z0-9]*(?:[ \t]*\+[ \t]*[A-Z][A-Z0-9]*)+\b", re.IGNORECASE)
_OPENING = re.compile(r"\b(?:DKL|DKR)\b", re.IGNORECASE)
_SPLIT = re.compile(r"\bTeilung\s*:?\s*(\d+)\s*mm\s+von\s+links\b", re.IGNORECASE)
_F004 = re.compile(r"\bF004\s+DK-Fenster\b", re.IGNORECASE)
_SIZE = re.compile(
    r"(?<![\w.,+-])([1-9][0-9]{1,4})\s*[x×]\s*([1-9][0-9]{1,4})(?![\d.,])"
    r"(?:\s*mm\b)?(?!\w|\s*(?:cm|m)\b)",
    re.IGNORECASE,
)

# Sales proposals for the reviewed size. Feasibility depends on the chosen system.
_WINDOW_VARIANTS = {
    (1500, 1000): (
        "Dwa skrzydła, słupek ruchomy",
        "Dwa skrzydła, słupek stały",
    ),
}


def _unique(values):
    values = set(values)
    return next(iter(values)) if len(values) == 1 else None


def inspect_german_offer_mail(text: str) -> list[dict]:
    """Separate positions and attach proposals without selecting a configuration."""
    blocks: list[list[str]] = []
    for source_line in text.splitlines():
        line = source_line.strip()
        if _POSITION.fullmatch(line):
            blocks.append([line])
        elif line and blocks:
            blocks[-1].append(line)

    positions = []
    for heading, *notes in blocks:
        _, name, description = _POSITION.fullmatch(heading).groups()
        product = "window" if name.casefold() == "fenster" else "entrance_door"
        details = [line for line in [description, *notes] if line]
        block = "\n".join([heading, *notes])
        sizes = [match for line in details for match in _SIZE.finditer(line)]
        width, height = map(int, sizes[0].groups()) if len(sizes) == 1 else (None, None)
        white = any(re.fullmatch(r"weiss\s*/\s*weiss", line.casefold()) for line in details)
        variants = ()
        if product == "window" and len(details) == 1 and _SIZE.fullmatch(details[0]):
            variants = _WINDOW_VARIANTS.get((width, height), ())
        layouts = ["".join(value.upper().split()) for value in _LAYOUT.findall(block)]
        construction = "F004 DK-Fenster" if product == "window" and not layouts and _F004.search(block) else None

        positions.append({
            "product_type": product,
            "width_mm": width,
            "height_mm": height,
            "quantity": _unique(map(int, _QUANTITY.findall(block))),
            "layout": _unique(layouts) if product == "window" else None,
            "construction": construction,
            "opening": _unique(value.upper() for value in _OPENING.findall(block)) if product == "window" else None,
            "split_from_left_mm": _unique(map(int, _SPLIT.findall(block))) if product == "window" else None,
            "profile": None,
            "color_inside": "white" if white else None,
            "color_outside": "white" if white else None,
            "source_lines": [heading, *notes],
            "proposed_variants": variants,
        })
    return positions
